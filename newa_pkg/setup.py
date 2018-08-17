import os, sys, shutil

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # "

EXECUTABLE = os.path.abspath(sys.executable)
INSTALLED_PATH = os.path.split(os.path.abspath(__file__))[0]
ROOT_PATH = EXECUTABLE[:EXECUTABLE.find('/bin/')]
CRON_PATH = os.path.join(ROOT_PATH, 'cron')

CRON_SCRIPTS = ( ('report_missing.py','newa/validation'),
               )
EXECUTABLE_SCRIPT_DIRS = ('newa/database', 'newa/history',
                          'newa/scripts', 'newa/validation')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # "

def read(*filepath):
    return open(os.path.join(os.path.dirname(__file__), *filepath)).read()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def setExecutable(script_path):
    file = open(script_path,'r')
    first_line = file.readline()
    if first_line.startswith('#!') and 'python' in first_line:
        the_rest = file.read()
        file.close()
        msg = 'updating path to python executable in'
        print msg, script_path[script_path.rfind('/rccpy/'):]
        file = open(script_path,'w')
        file.write('#! %s\n' % EXECUTABLE)
        file.write(the_rest)
        file.close()
        os.system('chmod 755 '+script_path)
        os.system('rm -f '+script_path+'c')
        return True
    return False

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def updateExectuables(script_dir):
    script_dirpath = os.path.join(INSTALLED_PATH, script_dir)
    if os.path.isdir(script_dirpath):
            for filename in os.listdir(script_dirpath):
                if filename.endswith('.py'):
                    script_path = os.path.join(script_dirpath, filename)
                    setExecutable(script_path)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def installCronScript(module_path, script_name):
    script_path = os.path.join(INSTALLED_PATH, module_path, script_name)
    script_path = os.path.normpath(script_path)
    if os.path.exists(script_path):
        cron_script_path = os.path.join(CRON_PATH, script_name)
        print 'copying %s to %s' % (script_path, cron_script_path)
        shutil.copyfile(script_path,cron_script_path)
        shutil.copymode(script_path,cron_script_path)
        shutil.copystat(script_path,cron_script_path)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

print 'working in installed path', INSTALLED_PATH
print 'system executable is', EXECUTABLE

# update executbale line in all scripts
for script_dir in EXECUTABLE_SCRIPT_DIRS:
    print 'updating executables in', script_dir
    updateExectuables(script_dir)

# install cron scripts
if 'cron' in sys.argv:
    if not os.path.exists(CRON_PATH): os.makedirs(CRON_PATH)
    for script_name, module_path in CRON_SCRIPTS:
        installCronScript(module_path, script_name)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
