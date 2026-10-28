import streamlit as st
from engine import ROOT, discover, review, RULES
st.set_page_config(page_title='Payment Rule Guard',layout='wide')
st.title('Payment Rule Guard · POC')
tab1,tab2,tab3=st.tabs(['Discover','Manage Rules','Developer Review'])
with tab1:
 st.write('Extract candidate payment rules from sample C# and SQL. Discovery is pattern-based and requires human approval.')
 if st.button('Discover rules'): st.success('Generated: '+', '.join(discover()))
with tab2:
 for rid,(title,desc,source,pattern) in RULES.items():
  draft=ROOT/'rules/drafts'/f'{rid}.md'; approved=ROOT/'rules/approved'/f'{rid}.md'
  with st.expander(f'{rid} · {title} · '+('Approved' if approved.exists() else 'Draft')):
   if draft.exists():
    content=st.text_area('Review/edit',draft.read_text(),key=rid,height=160)
    if st.button('Approve',key='approve'+rid):
     approved.parent.mkdir(exist_ok=True,parents=True)
     approved.write_text(content.replace('status: draft','status: approved'))
     st.success('Approved; commit this file to share it')
   else: st.info('Run discovery first')
with tab3:
 st.write('Checks staged Git files against approved rules.')
 if st.button('Review staged changes'):
  alerts=review()
  if alerts:
   for a in alerts: st.warning(a)
  else: st.info('No detectable violations in staged files; this does not guarantee correctness.')
 proposed=st.text_area('Paste proposed code or a question (optional)',height=160)
 if st.button('Ask AI'):
  try:
   from llm import explain
   context='\n'.join(p.read_text() for p in (ROOT/'rules/approved').glob('*.md'))[:12000]
   st.write(explain('Approved rules:\n'+context+'\nDeveloper input:\n'+proposed[:12000]))
  except Exception as e: st.error(f'LLM unavailable: {e}')

st.divider()
st.subheader('Business Owner Approval · POC')
st.caption('GitHub Environment reviewers provide actual approval. This page previews findings and the approval request; it does not bypass GitHub authorization.')
try:
 from approval import findings
 pending = findings()
 if pending:
  st.error(f'{len(pending)} approved business rule(s) potentially violated.')
  for finding in pending:
   with st.expander(f"{finding['id']} · {finding['title']}"):
    st.write(finding['description'])
    st.code(finding['source'])
  st.info('Open the GitHub pull request → Checks → RuleGuard Business Approval → Review deployments. An authorized reviewer can approve or reject the protected environment job.')
 else:
  st.success('No detected violations of approved rules in the current files.')
except Exception as exc:
 st.warning(f'Approval preview unavailable: {exc}')
