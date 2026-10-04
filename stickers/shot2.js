const { chromium } = require('playwright');
(async()=>{const b=await chromium.launch({executablePath:'/opt/pw-browsers/chromium-1194/chrome-linux/chrome'});
const p=await b.newPage({viewport:{width:1320,height:900},deviceScaleFactor:2});
await p.goto('file://'+process.cwd()+'/slap.html');await p.waitForTimeout(1500);await p.evaluate(()=>document.fonts.ready);
await p.screenshot({path:'slap-mockups.png',fullPage:true});await b.close();})();
