import base64
import hashlib
import struct

import requests


def test_multipart_file_upload_s3(
    app,
    file_service,
    s3_location,
    example_s3_file_record,
    identity_simple,
):
    
    recid = example_s3_file_record["id"]
    key = "dataset.bin"
    total_size = 17 * 1024 * 1024  # 17MB
    part_size = 10 * 1024 * 1024  # 10MB

    # total_size length, first 4 bytes are 00_00_00_00, second 00_00_00_01
    content = b"".join(struct.pack("<I", idx) for idx in range(0, total_size // 4))

    file_to_initialise = [
        {
            "key": key,
            "size": total_size,  # 2kB
            "metadata": {
                "description": "Published dataset.",
            },
            "transfer": {
                "type": "M",
                "parts": 2,
                "part_size": part_size,
            },
        }
    ]
    # Initialize file saving
    result = file_service.init_files(identity_simple, recid, file_to_initialise)
    result = result.to_dict()

    assert result["entries"][0]["key"] == key
    assert "parts" in result["entries"][0]["links"]

    def upload_part(part_url, part_content, part_size):
        part_checksum = base64.b64encode(hashlib.md5(part_content).digest())
        resp = requests.put(
            part_url,
            data=part_content,
            headers={
                "Content-Length": str(part_size),
                "Content-MD5": part_checksum,
            },
        )
        if resp.status_code != 200:
            raise Exception(f"Failed to upload part: {resp.text}")

    parts_by_number = {
        x["part"]: x["url"] for x in result["entries"][0]["links"]["parts"]
    }

    upload_part(parts_by_number[1], content[:part_size], part_size)

    upload_part(parts_by_number[2], content[part_size:], total_size - part_size)

    result = file_service.commit_file(identity_simple, recid, key).to_dict()
    assert result["key"] == file_to_initialise[0]["key"]

    # List files
    result = file_service.list_files(identity_simple, recid).to_dict()
    assert result["entries"][0]["key"] == file_to_initialise[0]["key"]
    assert result["entries"][0]["storage_class"] == "S"

    # Read file metadata
    result = file_service.read_file_metadata(identity_simple, recid, key).to_dict()
    assert result["key"] == file_to_initialise[0]["key"]
    assert result["transfer"]["type"] == "L"

    # Note: Invenio tests configure Celery tasks to run eagerly, so we cannot verify
    # whether the following checksum has actually been generated and stored in the
    # database. We assume it has been, as the processing of
    # `recompute_multipart_checksum_task` would have failed otherwise.
    # assert result["checksum"] == "multipart:562d3945b531e9c597d98b6bc7607a7d-2-10485760"

    # Instead, we test that the final MD5 checksum has been generated by the
    # `recompute_multipart_checksum_task`.
    assert result["checksum"] == "md5:a5a5934a531b88a83b63f6a64611d177"

    # Retrieve file
    result = file_service.get_file_content(identity_simple, recid, key)
    assert result.file_id == key

    # get the content from S3 and make sure it matches the original content
    sent_file = result.send_file()
    assert content == requests.get(sent_file.headers['Location']).content
