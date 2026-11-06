import os,pathlib,plistlib,shutil,subprocess,sys
root=pathlib.Path(__file__).resolve().parents[1]
p=root/'logs';p.mkdir(exist_ok=True)
agent=pathlib.Path.home()/'Library/LaunchAgents/local.nearone.refresh.plist';agent.parent.mkdir(parents=True,exist_ok=True)
config={'Label':'local.nearone.refresh','ProgramArguments':[sys.executable,str(root/'scripts/refresh.py'),'--discover'],'WorkingDirectory':str(root),'StartInterval':3600,'RunAtLoad':True,'EnvironmentVariables':{'NEARONE_SCHEDULED':'1'},'StandardOutPath':str(p/'refresh.log'),'StandardErrorPath':str(p/'refresh-error.log')}
if sys.platform!='darwin':sys.exit('ตัวติดตั้งนี้ใช้กับ macOS เท่านั้น')
subprocess.run(['launchctl','bootout',f'gui/{os.getuid()}',str(agent)],capture_output=True)
with agent.open('wb') as f:plistlib.dump(config,f)
subprocess.run(['launchctl','bootstrap',f'gui/{os.getuid()}',str(agent)],check=True)
print('เปิดการตรวจข้อมูลทุก 1 ชั่วโมงแล้ว จะทำงานเมื่อ Mac เปิดและเชื่อมต่ออินเทอร์เน็ต')
