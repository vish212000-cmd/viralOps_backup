import subprocess
import os

def find_deployed_commit():
    target_hash = 'index-Bv-npZDv.js'
    print(f"Looking for commit that produces: {target_hash}")
    
    # Get last 10 commits on main
    result = subprocess.run('git log -n 15 --oneline main', capture_output=True, text=True, shell=True)
    commits = [line.split()[0] for line in result.stdout.split('\n') if line]
    
    # Stash any local changes first
    subprocess.run('git stash', capture_output=True, shell=True)
    
    found = None
    try:
        for commit in commits:
            print(f"Checking commit {commit}...")
            subprocess.run(f'git checkout {commit}', capture_output=True, shell=True)
            subprocess.run('npm run build', capture_output=True, shell=True)
            
            assets_dir = os.path.join('dist', 'assets')
            if os.path.exists(assets_dir):
                files = os.listdir(assets_dir)
                if target_hash in files:
                    found = commit
                    print(f"\nSUCCESS! Found matching commit: {commit}")
                    break
    finally:
        # Restore state
        subprocess.run('git checkout feat/ai-graceful-degradation-clean', capture_output=True, shell=True)
        subprocess.run('git stash pop', capture_output=True, shell=True)
        
    return found

if __name__ == '__main__':
    find_deployed_commit()
