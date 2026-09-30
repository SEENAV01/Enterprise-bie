import unittest
from unittest.mock import Mock,patch
from h5_support import assert_error
from bie.evaluation.benchmarks.browser.served.lifecycle import navigate,ready,run_steps
class H5005(unittest.TestCase):
 def page(self):
  p=Mock();p.url='http://127.0.0.1:1/index.html';p.goto.return_value=Mock(status=200);p.reload.return_value=Mock(status=200);return p
 def test_navigate_real_url(self):
  p=self.page()
  with patch('bie.evaluation.benchmarks.browser.served.lifecycle.ready',return_value={'ready':True}):navigate(p,p.url,{},100)
  p.goto.assert_called_once();p.reload.assert_not_called()
 def test_reload_not_recreated_document(self):
  p=self.page()
  with patch('bie.evaluation.benchmarks.browser.served.lifecycle.ready',return_value={'ready':True}):navigate(p,p.url,{},100,reload=True)
  p.reload.assert_called_once();p.goto.assert_not_called()
 def test_admin_denial_classified(self):
  p=self.page();p.goto.side_effect=RuntimeError('net::ERR_BLOCKED_BY_ADMINISTRATOR');assert_error(self,lambda:navigate(p,p.url,{},100),'HTTP_NAVIGATION_ADMINISTRATOR_BLOCKED')
 def test_other_navigation_failure_blocks(self):
  p=self.page();p.goto.side_effect=RuntimeError('connection failed');assert_error(self,lambda:navigate(p,p.url,{},100),'HTTP_NAVIGATION_FAILED')
 def test_wrong_status_blocks(self):
  p=self.page();p.goto.return_value.status=404;assert_error(self,lambda:navigate(p,p.url,{},100),'HTTP_NAVIGATION_BINDING_FAILED')
 def test_redirect_not_accepted(self):
  p=self.page();assert_error(self,lambda:navigate(p,'http://127.0.0.1:1/other.html',{},100),'HTTP_NAVIGATION_BINDING_FAILED')
 def test_readiness_native_observation(self):
  with patch('bie.evaluation.benchmarks.browser.served.lifecycle.observe',return_value={'present':True,'visible':True,'text':'Ready'}):
   self.assertTrue(ready(Mock(),{'target':'#x','text':'Ready'},100)['ready'])
 def test_hidden_ready_not_enough(self):
  with patch('bie.evaluation.benchmarks.browser.served.lifecycle.observe',return_value={'present':True,'visible':False,'text':'Ready'}):
   assert_error(self,lambda:ready(Mock(),{'target':'#x','text':'Ready'},1),'HTTP_APP_READINESS_TIMEOUT')
 def test_async_poll_does_not_repeat_action(self):
  step={'checks':[{'target':'#x','property':'text','expected':'Ready'}]}
  row={'action_error':None,'observations':{'#x':{'present':True,'text':'Loading'}}}
  with patch('bie.evaluation.benchmarks.browser.actions.run_steps',return_value=[row]) as action,patch('bie.evaluation.benchmarks.browser.served.lifecycle.observe',return_value={'present':True,'text':'Ready'}):
   self.assertEqual(run_steps(Mock(),[step],100)[0]['observations']['#x']['text'],'Ready');action.assert_called_once()
