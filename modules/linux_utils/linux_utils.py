import paramiko
from loguru import logger
from pathlib import Path
import os

from paramiko import SSHClient

SSH_CONFIG = {
    'hostname': 'ec2-3-145-59-104.us-east-2.compute.amazonaws.com',
    'username': 'ubuntu',
    'key_filename': r'C:\Users\11627\Downloads\GrainedAI\WebAgentPipeline\reward_exp.pem',
    'remote_path': '/var/www/html/storage/frames_raw'
}


def init_ssh_client():
    """
    初始化SSH客户端连接

    Returns:
        paramiko.SSHClient: 已连接的SSH客户端，失败时返回None
    """
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        logger.info(f"Connecting to {SSH_CONFIG['hostname']}...")
        ssh_client.connect(
            hostname=SSH_CONFIG['hostname'],
            username=SSH_CONFIG['username'],
            key_filename=str(SSH_CONFIG['key_filename'])
        )

        logger.success("SSH connection established")
        return ssh_client

    except Exception as e:
        logger.error(f"Failed to establish SSH connection: {e}")
        return None


def upload_json_to_server(local_json_files: list[Path]):
    """
    通过SSH将JSON文件上传到AWS EC2服务器

    Args:
        local_json_files: 要上传的本地JSON文件路径列表
    """
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        logger.info(f"Connecting to {SSH_CONFIG['hostname']}...")
        ssh_client.connect(
            hostname=SSH_CONFIG['hostname'],
            username=SSH_CONFIG['username'],
            key_filename=str(SSH_CONFIG['key_filename'])
        )

        sftp = ssh_client.open_sftp()

        try:
            sftp.stat(SSH_CONFIG['remote_path'])
        except FileNotFoundError:
            logger.info(f"Creating remote directory: {SSH_CONFIG['remote_path']}")
            ssh_client.exec_command(f"sudo mkdir -p {SSH_CONFIG['remote_path']}")
            ssh_client.exec_command(f"sudo chown ubuntu:ubuntu {SSH_CONFIG['remote_path']}")

        uploaded_count = 0
        for local_file in local_json_files:
            try:
                remote_file_path = SSH_CONFIG['remote_path'] + local_file.name
                logger.info(f"Uploading {local_file.name} to {remote_file_path}")

                sftp.put(str(local_file), remote_file_path)
                uploaded_count += 1
                logger.success(f"Successfully uploaded {local_file.name}")

            except Exception as e:
                logger.error(f"Failed to upload {local_file.name}: {e}")

        sftp.close()
        ssh_client.close()

        logger.success(f"Upload completed. {uploaded_count}/{len(local_json_files)} files uploaded successfully.")

    except Exception as e:
        logger.error(f"Upload error: {e}")


def upload_images_to_server(image_paths) -> list[str]:
    """
    上传图片到服务器并返回文件名列表

    Args:
        image_paths: 本地图片路径列表

    Returns:
        list[str]: 上传成功的文件名列表
    """
    if not image_paths:
        return []

    uploaded_names = []
    try:
        ssh_client = paramiko.SSHClient()
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(
            hostname=SSH_CONFIG['hostname'],
            username=SSH_CONFIG['username'],
            key_filename=str(SSH_CONFIG['key_filename'])
        )
        sftp = ssh_client.open_sftp()

        # 确保远程目录存在
        # remote_dir = '/var/www/html/pickimgjson/hl/'
        remote_dir = '/var/www/html/storage/frames_raw/'
        try:
            sftp.stat(remote_dir)
        except FileNotFoundError:
            ssh_client.exec_command(f"sudo mkdir -p {remote_dir}")
            ssh_client.exec_command(f"sudo chown ubuntu:ubuntu {remote_dir}")

        # is_skip = True
        # 上传每张图片
        for img_path in image_paths:
            # if "nliKv22mGhY7LI4I8dAs2_raw.jpeg" in img_path.name:
            #     # break
            #     is_skip = False
            #
            # if is_skip:
            #     continue

            remote_path = remote_dir + img_path.name
            sftp.put(str(img_path), remote_path)
            uploaded_names.append(img_path.name)
            logger.debug(f"Uploaded {img_path.name}")

        sftp.close()
        ssh_client.close()
        logger.success(f"Uploaded {len(uploaded_names)} images")

    except Exception as e:
        logger.error(f"Failed to upload images: {e}")
        uploaded_names = [img.name for img in image_paths]  # 使用本地文件名

    return uploaded_names


def check_ssh_connection() -> bool:
    """检查SSH连接和配置"""
    key_file = Path(SSH_CONFIG['key_filename'])

    if not key_file.exists():
        logger.error(f"SSH key file not found: {key_file}")
        return False

    try:
        file_stat = key_file.stat()
        if os.name != 'nt':
            if oct(file_stat.st_mode)[-3:] != '400':
                logger.warning(f"SSH key file permissions may be too open. Consider running: chmod 400 {key_file}")
    except Exception as e:
        logger.warning(f"Could not check file permissions: {e}")

    return True


def list_remote_files(ssh_client, remote_path: str) -> list[str]:
    """
    列出远程目录中的所有文件

    Args:
        ssh_client: paramiko.SSHClient对象
        remote_path: 远程目录路径

    Returns:
        list[str]: 文件名列表，如果出错则返回空列表
    """
    if not ssh_client:
        logger.warning("⚠️ SSH client is None, creating new connection...")
        ssh_client = init_ssh_client()
        if ssh_client is None:
            logger.error("❌ Failed to create SSH connection")
            return []

    try:
        # 使用SFTP方式列出文件
        sftp = ssh_client.open_sftp()
        files = sftp.listdir(remote_path)
        sftp.close()

        logger.info(f"📁 Found {len(files)} items in {remote_path}")
        return files

    except FileNotFoundError:
        logger.warning(f"📂 Directory not found: {remote_path}")
        return []
    except Exception as e:
        logger.error(f"💥 Error listing files in {remote_path}: {e}")
        return []


def backup_existing_images(ssh_client, remote_dir, search_string):
    """查找包含字符串的文件并添加备份后缀"""
    from datetime import datetime

    today = datetime.now().strftime("%Y%m%d")

    # 连接SSH
    if not ssh_client:
        logger.warning("⚠️ SSH client is None, creating new connection...")
        ssh_client = init_ssh_client()
        if ssh_client is None:
            logger.error("❌ Failed to create SSH connection")
            return

    # 查找包含字符串的文件
    find_cmd = f'find {remote_dir} -name "*{search_string}*" -type f'
    stdin, stdout, stderr = ssh_client.exec_command(find_cmd)

    files = [line.strip() for line in stdout.readlines()]

    # 给每个文件添加备份后缀
    for file_path in files:
        new_path = f"{file_path}_bak_{today}"
        rename_cmd = f'mv "{file_path}" "{new_path}"'
        ssh_client.exec_command(rename_cmd)
        logger.info(f"备份: {file_path} -> {new_path}")

    ssh_client.close()
    logger.success(f"完成，共备份 {len(files)} 个文件")


def replace_step_id_in_filenames(ssh_client, remote_dir, source_step_id, target_step_id):
    """查找包含source_step_id的文件，复制一份并将副本文件名中的source_step_id替换成target_step_id"""

    # 连接SSH
    if not ssh_client:
        logger.warning("⚠️ SSH client is None, creating new connection...")
        ssh_client = init_ssh_client()
        if ssh_client is None:
            logger.error("❌ Failed to create SSH connection")
            return

    # 查找包含source_step_id的文件
    find_cmd = f'find {remote_dir} -name "*{source_step_id}*" -type f'
    stdin, stdout, stderr = ssh_client.exec_command(find_cmd)

    files = [line.strip() for line in stdout.readlines()]

    # 复制文件并重命名
    for file_path in files:
        # 生成新文件名（将source_step_id替换为target_step_id）
        new_path = file_path.replace(source_step_id, target_step_id)

        # 复制文件
        copy_cmd = f'cp "{file_path}" "{new_path}"'
        ssh_client.exec_command(copy_cmd)
        logger.info(f"复制: {file_path} -> {new_path}")

    ssh_client.close()
    logger.success(f"完成，共复制 {len(files)} 个文件")