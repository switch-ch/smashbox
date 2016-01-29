__doc__ = """ Test designed to cread a high load on the server by syncing, massively sharing and deleting an unpacked linux kernel. 
              The goal is not to test any particular functionality, but the behaviour under high load.
"""

from smashbox.utilities import * 
from smashbox.script import config

import glob
import urllib
import os.path
#import pydevd
import tarfile
import subprocess
import shutil

num_owners = int(config.get('num_owners',1))
num_sharers = int(config.get('num_sharers_per_owner',1))
num_synching_sharers = int(config.get('num_synching_sharers_per_owner',1))

testsets = [
            {"num_owners":1,"num_sharers_per_owner":1, "num_synching_sharers_per_owner":1},
            {"num_owners":2,"num_sharers_per_owner":2, "num_synching_sharers_per_owner":1},
            {"num_owners":3,"num_sharers_per_owner":3, "num_synching_sharers_per_owner":1},
            {"num_owners":4,"num_sharers_per_owner":4, "num_synching_sharers_per_owner":1},
            {"num_owners":5,"num_sharers_per_owner":5, "num_synching_sharers_per_owner":1},
            {"num_owners":6,"num_sharers_per_owner":6, "num_synching_sharers_per_owner":1},
            {"num_owners":7,"num_sharers_per_owner":7, "num_synching_sharers_per_owner":1},
            {"num_owners":8,"num_sharers_per_owner":8, "num_synching_sharers_per_owner":1},
            {"num_owners":9,"num_sharers_per_owner":9, "num_synching_sharers_per_owner":1},
            {"num_owners":10,"num_sharers_per_owner":10, "num_synching_sharers_per_owner":1}
            ]

num_users = num_owners + ( num_owners*num_sharers)
logger.info("num_owners:%i; num_sharers:%i; num_synching_sharers:%i; num_users:%i"%(num_owners,num_sharers,num_synching_sharers,num_users))

data_dir_name = "loadtestdata"
download_url1 = config.get('download_url1', 'https://cdn.kernel.org/pub/linux/kernel/v4.x/linux-4.0.tar.xz')
download_url2 = config.get('download_url2', 'https://cdn.kernel.org/pub/linux/kernel/v4.x/linux-4.3.tar.xz')
tar_file_name1 = config.get('tar_file_name1', 'linux-4.0.tar.xz')
tar_file_name2 = config.get('tar_file_name2', 'linux-4.3.tar.xz')
unpacked_dir_name = 'data'
unpacked_dir_name1 = config.get('unpacked_dir_name1', 'linux-4.0')
unpacked_dir_name2 = config.get('unpacked_dir_name2', 'linux-4.3')
data_dir = os.path.join(config.rundir, "..", data_dir_name)

tar_file1 = os.path.join(data_dir, tar_file_name1)
tar_file2 = os.path.join(data_dir, tar_file_name2)

OCS_PERMISSION_READ = 1
OCS_PERMISSION_UPDATE = 2
OCS_PERMISSION_CREATE = 4
OCS_PERMISSION_DELETE = 8
OCS_PERMISSION_SHARE = 16
OCS_PERMISSION_ALL = 31

@add_worker
def setup(step):

    step (1, 'create test users and download test data')
    reset_owncloud_account(reset_procedure='keep', num_test_users=num_users)
    check_users(num_users)

    reset_rundir()

    if not os.path.exists(data_dir):
        os.mkdir(data_dir)
    
    if not os.path.isfile(tar_file1):
        logger.info("downloading tar file1...")
        urllib.urlretrieve(download_url1, filename=os.path.join(data_dir, tar_file_name1))
    if not os.path.isfile(tar_file2):
        logger.info("downloading tar file2...")
        urllib.urlretrieve(download_url2, filename=os.path.join(data_dir, tar_file_name2))

def create_sharer(sharer_id):
    user_data_dir = os.path.join(data_dir, `sharer_id`)
    #oc_sharer_id = ((sharer_id -1) * (num_sharers + 1)) + 1
    oc_sharer_id = sharer_id

    unpacked_dir1 = os.path.join(data_dir, `sharer_id`, unpacked_dir_name1)
    unpacked_dir2 = os.path.join(data_dir, `sharer_id`, unpacked_dir_name2)

    def sharer(step):
        #pydevd.settrace("10.254.0.1")
        step (2, 'unpack test data')
        if not os.path.exists(os.path.join(user_data_dir, unpacked_dir_name1)):
            if not os.path.exists(user_data_dir):
                os.mkdir(user_data_dir)
            subprocess.call(["/bin/tar", "-xf", tar_file1, "-C", user_data_dir])
        if not os.path.exists(os.path.join(user_data_dir, unpacked_dir_name2)):
            subprocess.call(["/bin/tar", "-xf", tar_file2, "-C", user_data_dir])
    
        step (3, 'Create workdir')
        d = make_workdir()
    
        step (4, 'Create initial test files and directories')
    
        share_dir = os.path.join(d, unpacked_dir_name)
        shutil.move(unpacked_dir1, share_dir)
        #mkdir(share_dir)
        #createfile(os.path.join(share_dir,'TEST_FILE_USER_SHARE.dat'),'0',count=1000,bs=100)
    
        step (10, 'initial sync')
        
        run_ocsync(d,user_num=oc_sharer_id)
    
        #subprocess.call(["/usr/bin/sudo", "/bin/mount", "--bind", unpacked_dir, mountpoint])
        #os.symlink(unpacked_dir, os.path.join(d, unpacked_dir_name))
        
        step (20, 'Sharer shares directory')
    
        shared = reflection.getSharedObject()
        user_sharer = "%s%i"%(config.oc_account_name, oc_sharer_id)
        
        kwargs = {'perms': OCS_PERMISSION_ALL}
        for sharee_id in range(1, num_sharers+1):
            #oc_sharee_id = oc_sharer_id + sharee_id
            oc_sharee_id = num_owners + (sharer_id-1)*num_sharers + sharee_id
            user_sharee = "%s%i"%(config.oc_account_name, oc_sharee_id)
            shared['SHARE_LOCAL_DIR%i'%(oc_sharee_id)] = share_file_with_user (unpacked_dir_name, user_sharer, user_sharee, **kwargs)
    
        step (30, 'endless test')
        
        while True:
            shutil.move(share_dir, unpacked_dir1)
            shutil.move(unpacked_dir2, share_dir)
            run_ocsync(d,user_num=oc_sharer_id)
            shutil.move(share_dir, unpacked_dir2)
            shutil.move(unpacked_dir1, share_dir)
            run_ocsync(d,user_num=oc_sharer_id)

    add_worker(sharer,'sharer%d'%sharer_id)
    for sharee_id in range(1, num_synching_sharers+1):
        #oc_sharee_id = oc_sharer_id + sharee_id
        oc_sharee_id = num_owners + (sharer_id-1)*num_sharers + sharee_id

        def sharee(step):
            #pydevd.settrace("10.254.0.1")
            step (2, 'Create workdir')
            d = make_workdir()
        
            step (25, 'Download shared directory')
        
            run_ocsync(d,user_num=oc_sharee_id)
            #list_files(d)
            
            step (30, 'endless test')
            while True:
                run_ocsync(d,user_num=oc_sharee_id)

        add_worker(sharee, 'sharee%d_%d'%(sharer_id,sharee_id))

for sharer_id in range(1, num_owners+1):
    create_sharer(sharer_id)




