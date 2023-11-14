import datetime
import os
import pathlib
import shutil
import sqlite3

from pydub import AudioSegment
from pydub.exceptions import CouldntDecodeError

AudioSegment.converter = r"C:\Windows\System32\ffmpeg.exe"
AudioSegment.ffmpeg = r"C:\Windows\System32\ffmpeg.exe"
AudioSegment.ffprobe = r"C:\Windows\System32\ffprobe.exe"

account_name = "账户1"
base_dir = os.path.expanduser(f"~/AppData/Roaming/Anki2/{account_name}")
media_folder = os.path.join(base_dir, "collection.media")  # 指定源文件夹
anki_db_path = os.path.join(base_dir, "collection.anki2")


def convert_ogg(src_folder):
    i = 0
    for file_name in os.listdir(pathlib.Path(src_folder).absolute()):
        if file_name.endswith(".ogg"):
            ogg_path = os.path.join(src_folder, file_name)
            try:
                ogg_audio = AudioSegment.from_ogg(ogg_path)
                mp3_path = os.path.splitext(ogg_path)[0] + ".mp3"

                # 导出音频到mp3
                ogg_audio.export(mp3_path, format="mp3")
                print("Converted: " + file_name)

                # 删除源.ogg文件
                os.remove(ogg_path)

                i += 1
            except CouldntDecodeError:
                # 若出现错误则跳过当前文件
                print("Failed to convert: " + file_name)
                continue
        return i


def backup_db(db_path):
    # 获取当前时间，作为备份文件的名字一部分
    current_time = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    # 创建备份文件路径
    backup_path = os.path.join(os.path.dirname(db_path), f"backup-{current_time}.anki2")

    # 复制文件来创建备份
    shutil.copy2(db_path, backup_path)
    print(f"Database backup has been created at {backup_path}")


def batch_rename_apkg(db_path):
    # 创建一个数据库连接
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("updating notes...")

    # 提取所有含有".ogg"的条目
    cursor.execute(
        """
    SELECT *
    FROM notes
    WHERE flds LIKE '%.ogg%'
    """
    )

    # 提取到的entries
    rows = cursor.fetchall()

    # 循环获取每一条数据
    for row in rows:
        # 旧内容
        old_content = row[6]

        # 替换为新内容
        new_content = old_content.replace(".ogg", ".mp3")
        # 更新内容
        cursor.execute(
            """
        UPDATE notes
        SET flds = ?
        WHERE id = ?
        """,
            (
                new_content,
                row[0],
            ),
        )

    # 提交修改的操作到数据库
    conn.commit()

    # 关闭数据库连接
    conn.close()


file_changed = convert_ogg(media_folder)

if file_changed > 0:
    # 创建数据库备份
    backup_db(anki_db_path)

    # 对Anki库中的所有卡片进行批量修改
    batch_rename_apkg(anki_db_path)
else:
    print("nothing to do, quit")
