/* Real offline browser workflow. Set PLAYWRIGHT_MODULE to an installed playwright module. */
const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright')
const fs=require('fs'),path=require('path'),assert=require('assert')
const base=process.env.EXAM_QA_URL||'http://127.0.0.1:8875'
const out=process.env.EXAM_QA_OUTPUT||path.resolve(__dirname,'../../qa/browser')
fs.mkdirSync(out,{recursive:true})
const results=[],errors=[],external=[]
function log(name){results.push({name,status:'passed'});console.log('PASS '+name)}
async function run(){
 const browser=await chromium.launch({headless:true,...(process.env.EXAM_QA_BROWSER?{executablePath:process.env.EXAM_QA_BROWSER}:{})})
 const context=await browser.newContext({viewport:{width:1440,height:1000},locale:'zh-CN'})
 await context.route('**/*',route=>{if(!route.request().url().startsWith(base)){external.push(route.request().url());return route.abort()}return route.continue()})
 const page=await context.newPage()
 page.on('pageerror',e=>errors.push(e.message))
 page.on('response',res=>{if(res.status()>=500)errors.push(`HTTP ${res.status()} ${res.url()}`)})
 async function screenshot(name){await page.locator('.skeleton-grid').waitFor({state:'hidden'});await page.screenshot({path:path.join(out,name+'.png'),fullPage:true,animations:'disabled'})}
 async function visit(route,title){await page.goto(base+route);if(title)await page.getByRole('heading',{name:title,exact:true}).waitFor();await page.waitForTimeout(300);assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'overflow '+route);log('route '+route)}
 async function login(role){await page.goto(base+'/login');await page.getByRole('button',{name:role==='admin'?'管理员':'普通用户',exact:true}).click();await page.getByRole('button',{name:'登录工作台',exact:true}).click();await page.getByRole('heading',{name:new RegExp(role+'，从这里开始')}).waitFor();log('login '+role)}
 await visit('/login','欢迎回来');await screenshot('01_login_desktop')
 await login('demo');await screenshot('02_dashboard_desktop')
 await page.getByRole('button',{name:'打开演示导航',exact:true}).click();await page.getByRole('complementary',{name:'功能演示导航'}).waitFor();await screenshot('03_demo_guide');await page.getByRole('button',{name:'关闭演示导航',exact:true}).click();log('demo guide')
 await visit('/catalog/civil','公务员报考');await screenshot('04_catalog')
 const first=page.locator('.opportunity-title').first();await first.click();await page.getByRole('button',{name:'开始资格匹配',exact:true}).waitFor();await page.getByRole('button',{name:'开始资格匹配',exact:true}).click();await page.locator('.matching-result').waitFor();log('qualification matching')
 await page.getByRole('button',{name:'记录报考',exact:true}).click();await page.getByLabel('报考姓名',{exact:true}).fill('QA 演示同学');await page.getByLabel('联系方式',{exact:true}).fill('演示联系方式');await page.getByRole('button',{name:'保存报考记录',exact:true}).click();await page.getByRole('dialog').waitFor({state:'hidden'});log('application submission')
 await visit('/applications','我的报考');await page.getByRole('article').filter({hasText:'QA 演示同学'}).waitFor();await screenshot('05_applications')
 await page.getByRole('button',{name:'完善记录',exact:true}).first().click();await page.getByLabel('备注',{exact:true}).fill('QA 已补充材料');await page.getByRole('button',{name:'更新并重新提交',exact:true}).click();await page.getByRole('dialog').waitFor({state:'hidden'});log('application update and resubmit')
 await page.getByRole('button',{name:'新增计划',exact:true}).click();await page.getByLabel('计划标题',{exact:true}).fill('QA 明天的考试');await page.getByLabel('考试日期',{exact:true}).fill(new Date(Date.now()+86400000).toISOString().slice(0,10));await page.getByRole('button',{name:'保存计划',exact:true}).click();await page.getByRole('dialog').waitFor({state:'hidden'});log('application plan')
 await visit('/services','公共服务');await screenshot('06_services');await page.getByRole('button',{name:'提交咨询',exact:true}).first().click();await page.getByLabel('咨询主题',{exact:true}).fill('QA 材料咨询');await page.getByLabel('问题描述',{exact:true}).fill('请帮助确认需要准备哪些材料。');await page.getByRole('button',{name:'提交咨询',exact:true}).last().click();await page.getByRole('dialog').waitFor({state:'hidden'});await page.getByRole('heading',{name:'QA 材料咨询',exact:true}).waitFor();log('service request')
 await visit('/profile','个人中心');await page.getByLabel('昵称',{exact:true}).fill('QA 同学');await page.getByRole('button',{name:'保存档案',exact:true}).click();await page.getByText('个人档案已保存',{exact:true}).waitFor();log('profile persistence')
 await visit('/recommendations','发现适合你的方向');await screenshot('07_recommendations')
 await visit('/practice','在线刷题');await page.getByRole('button',{name:'生成练习卷',exact:true}).click();await page.getByLabel('题目数量',{exact:true}).fill('3');await page.getByLabel('考试时长（分钟）',{exact:true}).fill('5');await page.getByRole('button',{name:'生成试卷',exact:true}).click();await page.getByRole('dialog').waitFor({state:'hidden'});log('generate paper')
 await page.getByRole('button',{name:'开始考试',exact:true}).first().click();await page.getByRole('heading',{name:'答题卡',exact:true}).waitFor();await page.locator('.answer-option').first().click();await page.getByRole('button',{name:'保存答案',exact:true}).click();await page.getByText('答案已保存',{exact:true}).waitFor();await screenshot('08_exam');await page.reload();await page.locator('.answer-option.selected').waitFor();log('exam resume')
 page.once('dialog',d=>d.accept());await page.getByRole('button',{name:'交卷并查看报告',exact:true}).click();await page.getByRole('heading',{name:'本次练习已完成',exact:true}).waitFor();await screenshot('09_exam_report');log('exam submit')
 await visit('/scores','学习报告');await screenshot('10_scores');await visit('/notifications','消息中心');await visit('/favorites','收藏与比较');await visit('/notices','公告资讯');await visit('/catalog/institution','事业单位报考');await visit('/catalog/graduate','研究生报考')
 await page.getByRole('button',{name:'退出登录',exact:true}).click();await page.getByRole('heading',{name:'欢迎回来',exact:true}).waitFor();await login('admin');await visit('/admin','管理空间')
 await visit('/admin/applications','报考数据');await screenshot('11_admin_applications');const appRow=page.getByRole('row').filter({hasText:'QA 演示同学'});await appRow.getByRole('button',{name:'审核报考记录',exact:true}).click();await page.getByLabel('状态',{exact:true}).selectOption('approved');await page.getByLabel('审核说明',{exact:true}).fill('QA 已核对材料，请继续准备。');await page.getByLabel('成绩',{exact:true}).fill('92');await page.getByRole('button',{name:'保存记录',exact:true}).click();await page.getByRole('dialog').waitFor({state:'hidden'});await appRow.getByText('审核通过',{exact:true}).waitFor();log('admin application review')
 const exported=page.waitForEvent('download');await page.getByRole('button',{name:'导出',exact:true}).click();await (await exported).saveAs(path.join(out,'applications_export.xlsx'));log('admin application export')
 await visit('/admin/service-requests','公共服务咨询');const ticket=page.getByRole('row').filter({hasText:'QA 材料咨询'});await ticket.getByRole('button',{name:'编辑记录',exact:true}).click();await page.getByLabel('状态',{exact:true}).selectOption('answered');await page.getByLabel('回复内容',{exact:true}).fill('QA 请查看公共服务中的材料清单。');await page.getByRole('button',{name:'保存记录',exact:true}).click();await page.getByRole('dialog').waitFor({state:'hidden'});log('admin service reply')
 for(const [r,t] of [['users','用户权限'],['opportunities','招考信息'],['notices','公告资讯'],['questions','题库管理'],['papers','试卷管理'],['notifications','消息通知'],['services','公共服务资源'],['historical-stats','历史招考统计'],['recommendation-rules','推荐权重'],['requirement-rules','资格匹配规则'],['settings','系统设置']])await visit('/admin/'+r,t)
 await visit('/admin/operations','系统运行');await page.getByRole('button',{name:'创建备份',exact:true}).click();await page.locator('.backup-row').first().waitFor();await screenshot('12_operations');log('backup creation')
 await page.setViewportSize({width:390,height:844});for(const[r,t]of [['/','admin，从这里开始。'],['/services','公共服务'],['/catalog/civil','公务员报考'],['/admin/applications','报考数据']]){await visit(r,t)}await screenshot('13_mobile_admin');await page.getByRole('button',{name:'打开导航',exact:true}).click();await page.locator('.sidebar.open').waitFor();await screenshot('14_mobile_navigation');await page.locator('.sidebar-shade').click({position:{x:375,y:400}});log('mobile navigation')
 await page.getByRole('button',{name:'退出登录',exact:true}).click();await page.goto(base+'/login');await page.emulateMedia({reducedMotion:'reduce'});await screenshot('15_mobile_login');const animated=await page.locator('.orb-a').evaluate(el=>getComputedStyle(el).animationName);assert.equal(animated,'none');log('reduced motion')
 assert.equal(external.length,0,'external network requests: '+external.join(','));assert.equal(errors.length,0,errors.join('\n'));log('no external requests or runtime errors')
 await browser.close();fs.writeFileSync(path.join(out,'browser_results.json'),JSON.stringify({base,results,errors,external},null,2));console.log('ALL PASSED '+results.length)
}
run().catch(error=>{fs.writeFileSync(path.join(out,'browser_failure.json'),JSON.stringify({results,errors,external,error:error.stack},null,2));console.error(error);process.exit(1)})
