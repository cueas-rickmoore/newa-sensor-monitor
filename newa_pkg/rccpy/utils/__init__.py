
import os, shutil

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

class BogusValue:
    def __str__(self): return 'BOGUS VALUE'
BOGUS_VALUE = BogusValue()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def backupFile(abs_filepath, backup_dirpath=None):
    if backup_dirpath is None:
        backup_filepath_ = abs_filepath
    else:
        dirpath, filename = os.path.split(abs_filepath)
        dirpath_ = os.path.normpath(backup_dirpath)
        backup_filepath_ = os.path.join(dirpath_, filename)

    backup_filepath = backup_filepath_ + '.backup'
    count = 0
    while os.path.exists(backup_filepath):
        count += 1
        backup_filepath = backup_filepath_ + '.backup%03d' % count
    shutil.copyfile(abs_filepath, backup_filepath)
    shutil.copymode(abs_filepath, backup_filepath)
    shutil.copystat(abs_filepath, backup_filepath)

    return backup_filepath

