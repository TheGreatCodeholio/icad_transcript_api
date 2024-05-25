#!/home/icad/.venv/bin/python
import argparse
import os
import secrets
import subprocess


def generate_secure_token(length=64):
    return secrets.token_hex(length)


def create_folder_paths(working_path):
    config_path = os.path.join(working_path, "etc")
    model_path = os.path.join(working_path, "models")
    log_path = os.path.join(working_path, "log")

    if not os.path.exists(config_path):
        os.mkdir(config_path)

    if not os.path.exists(model_path):
        os.mkdir(model_path)

    if not os.path.exists(log_path):
        os.mkdir(log_path)


def generate_env_file(working_path):
    env_content = f"""
# Flask Secret Key
SECRET_KEY='{os.urandom(24).hex()}'
WORKING_PATH={working_path}
TRANSFORMERS_CACHE=/app/models
"""

    env_file_path = os.path.join(working_path, '.env')
    with open(env_file_path, 'w') as file:
        file.write(env_content)

    os.chmod(env_file_path, 0o600)
    print(f"Generated .env file in {working_path} with random passwords and set permissions to 600.")


def run_docker_compose():
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
    print("Docker Compose has started the services.")


def update_services():
    subprocess.run(["docker", "compose", "pull"], check=True)
    subprocess.run(["docker", "compose", "up", "-d"], check=True)
    print("Services have been updated.")


def reset_services(working_path):
    # Stop and remove all containers, networks, and volumes associated with the project
    subprocess.run(["docker", "compose", "down", "-v"], check=True)
    print("Stopped and removed all project containers, networks, and volumes.")

    # Remove .env file if it exists
    env_file_path = os.path.join(working_path, '.env')
    if os.path.exists(env_file_path):
        os.remove(env_file_path)
        print(f"Removed Environment Variables from {env_file_path}: .env")

    generate_env_file(working_path)
    subprocess.run(["docker", "compose", "pull"], check=True)
    run_docker_compose()
    print("Services have been reset and started with new configurations.")


def main():
    parser = argparse.ArgumentParser(description='Manage iCAD Transcribe Docker service.')
    parser.add_argument('-a', '--action', choices=['init', 'update', 'reset'], help='Action to perform')
    working_path = os.getcwd()

    args = parser.parse_args()

    if working_path is None:
        print("Missing required arguments. Must provide --action")
        return

    create_folder_paths(working_path)

    if args.action == 'init':
        generate_env_file(working_path)
        run_docker_compose()
    elif args.action == 'update':
        update_services()
    elif args.action == 'reset':
        reset_services(working_path)
    else:
        print("No valid action specified. Use --action with 'init', 'update', or 'reset'.")


if __name__ == "__main__":
    main()
