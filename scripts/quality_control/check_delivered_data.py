import os
from pathlib import Path
import json
import time
from loguru import logger
from pydantic.json_schema import model_json_schema

from modules.webagent_data_utils import WebAgentFlow

file_path = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_modification/modification/20250708/all_generated_delivered_merged_modified")
delivered = Path("/Users/anthonyf/projects/grainedAI/WebAgentPipeline_storage/src/all_delivered/all_delivered_20250708_before_merge")
d_json_paths = delivered.glob('*.json')
json_paths = file_path.glob('*.json')
skip_ids = {'avTJZLR_V3GrC6Zej4JZB', 'iGPtAHZUU5mFTj4wb_z-N', '3OofEguwR6SQ_j6lVquY-', 'kC7e_ezMrLeXFb6_-zDzO', 'TzaaRmAxXr-1V0GFrhtFL', 'ZRDPQeY7pD1rN7zQ2z8OL', 'NQGFPb2PdIHbnkxaqlGFF', '9Lf9sJQnRuh-oHZtd0jFA', 'KmsnuTyOMYq0PyRJbtNgM', 'FyVlFd43JWHoGM2tZobNA', '8bLIWKjxf89GDr1OAgHfZ', '109nhEZB8MLmmrDZCcjCf', 'h9MR5CQTETCbk2P1HiLJF', 'Obanv3eRpkbPdqEFX5kml', 'Xh-xFiaQxFckCttNbpEBu', 'LvCNp3RsnKh0VoS8F-adV', 'DHTKhg1RsYazZrCL0I09p', 'whrXbcKFrKeKZ7LWLyHkQ', '01GzBXE8QAieaFJvl58I5', 'xpapbnhU2eAKJ__EkH98L', 'ndXjVL4787n8LNX3M5JQ-', 'OiDxFQ6s0_nIeclsvmvA8', 'hPmtvNK2ouFTvqgsjMf2O', 'f4qiGH3wA4fsoynHcuIEA', 'TziL-I9GZCZDyDJRnMjJB', 'zI-HlooK5M35D116SWyMi', '2lyQm-Mp57mafQUIzTPxB', '1BLkNsDZC30XrTTzSFXSW', 'Uam59X9OXm5ldNHCdtR14', 'kFaJftb76dPWT9FJ5rWX7', 'tV821tBv9jNadtpf9hqPD', 'tD9NDrhgrQ0JymycH_7iA', 'WevUqeJFRvYFRiwbEo04y', 'Grpsz-6mznPpzk7lZZmFw', 'VjjfiCUk-aJIaMQkXfzuz', '2hYO-D_2c2ISfWa1__OZf', 'Zr5Xv_IMjA3sagqeoDVQv', '4jMDnQ7E7Ny8yg-bBYrHz', 'Hc89VEEyZcCRROD09jXFR', 'bK9XvpEwo43TQPlL-20uh', 'khiG9vKWaMjxQo4ld1Kan', '1TgIrvy5qlme6dUWen6fo', 'KKLAyLGC_fkmKBBP5dMUP', 'ymq-b3ICLLwS-pXn3W8vL', 'Y7TQDYWjLLgv7pf8O0Bfe', 'l0fwNJhDzN8ewDj6uhQVF', 'zqJ39_WGkasH7G2bytqTx', 'Nl7relU0BZgcffB_tnXUO', 'i64-kFW8FpUSVTv5QW2Ni', 'rucLfBiHLG7DUWhYmUPfg', 'acBs29Oo9N2QOD32XIWc3', '7WG2Pq3WvaDAaT3Obe_ze', 'z43Vi-DpLQT1xlk4zCRHS', 'QNqRIv38_4nRBmR_r5Qoj', '_Odt1xZfbVGHKpFtFUt-8', 'm6o3L1pfOKRGjKq_KFFE0', 'hpc0Wu1RudwW69WVPHm1G', 'TFRkY9cwo54_r91NpBjIx', 'aa7OJH9oeaNUeR_LTgxY7', 'bh49j153VqgCmyUpm8FXK', 'Y3Cqu0cD09946waxHIgP0', 'w42mpt5WBDUhkkdqMSHN2', 'UcEUn5wqPSvLgm_B1vX5d', 'mOgWPE3VZM2tBK4ZDbLWQ', 'lox4NgFBHzWTRI9KMxtHx', 'plBOcI2fuUbwv0676tC3G', 'x9IMOUmxyMrY0vPhMLb9S', '5Jdzn47aUPPrVgPGEw1Q8', 'AI6JJx_GAA5A7y0Zu17O3', 'e2aWce1e_Az-aHi3AlqSY', 'kXhsIGajzoziQdIipGAO3', 'sn3Uglpimlpri3vFzCPoe', 'KS-vcCtykWd9TNq-DJz_I', 'faPeTAaYxF2xJmWc625cP', 'i0frqL_GvTfzVt_R_5Kn5', 'vQYqajGQWucV35nRqivqE', 'X9GecA56UBA0r4WJ4Pm6O', 'GqdWcn1f6ewcJdNqoaqMQ', 'Q35N8b7jQMxaDYdmTvasV', 'v30--vW-xlNvlk47VeY62', '08dZMizSs3_oTfaGgF1Fz', 'm2GA-SwpjKXGF-5gf2Kh4', 'YjPqBaahTn6uk0-BltGoZ', 'wLq7svsp_Xxc0bQVnsuzl', 'gOORYKBuFAWfr66PSMMHU', '4O040c6TKobZeR1Nl6nf5', 'VuojtFU4iX8CHLTvC95lh', 'qh7j8AVbrygMsSXGLd5ud', '1YNd-CaECndASGPcQ89fM', '3I7Zkz7dpdvsgxR2xNw2n', '-HnjgN2Sz8DoMt7PH3YKN', 'eOM95I4btPkIK6HaAJi5l', 'C85Mu3ShWriYd7dzANQXz', 'EU-n2NK1pBkS6HgMCecEY', '7aITmNWY9GbDn6EgvtvAa', '9Z_19-A3vPSSRIL5QIUQ8', 'hT5zjY8BV9TnW14Vtz1Y3', '28rnm48tPGCPBKVR3Jg62', 'HWaCn3Scajz8N8NSRy3v1', 'LTBSFpwoox5IaT870EA42', 'kOqAFjE2IjWZoiUHTYMpV', 'PWrm-QAYi-rMdCoA62xQx', 'CDQXl_HIoThoXnMVe__T3', 'eiek-tc12zBhPsJOw48RT', 'HtueQJ93x5K8c9NP_4oTp', 'Cb0clWppbp9KrczIpzGoY', 'n1cHPgLVD5iRqEhuk7HjC', 'zIVlANbywlLZYyBcR5d8U', 'f_ByB6EChEkGoRWNKree8', 'IKduwCzu4E-nNfaYtRUEn', '0l-FVGQZlKkrX26Qx9Hwd', 'F_fzaLS59eOYw0RKne1vK', 'QBre-OYnDp2_u0paqReYB', 'ExiH124x3p95hXPyFU0bI', '01ekEGOp5PXIZ60zfIu41', '533FPcI4YfUdTOr1a_J3F', '5oQbBXKfc-xDyVpRNlRsT', 'xf0WcZTAQDvmv6HHCQUFS', 'Uwv_Yddc8FGKko0IC-Xr-', 'T10g0iN-HhxrHPqSjMwQM', 'X1S1juYvLnwObvYuZH9cx', 'a4DIPQsDkAd6K4TM8Gwm4', 'zNJLx6v-ti2eGzn1OtNfN', 'f3KWQ5fI8uAYayqXRcPs4', '6hjFZQ05Go2WuVBvfiZi8', 'USic5kF3Zbs3Cg2VYw7u-', 'D4vRtVQaxcEPXroHJMxu-', '6tLdm15_y-RnVqwiBXaFW', 'Dxy_s3PLrApHcYSxlMsPw', 'jkkpFLX6ISLWvqYVluFxY', 'A0Bla-A9jhcw3heq0A8rC', '2i-pDOW-3r_PWsLoz3Uks', 'NAUvmTPfY68i_XUxAk_b6', 'JiXfw1AxMK41QfOlj8YqC', 'WyzkBV1Zzi8rl3WIQCjlA', 'OPcfPhKIynoXtUO5mEpl0', '20I0n_JapNAYtDMhnkXbl', 'S6e00iGf2b0UE5ouOrsVa', 'Kuj2z2Kvjv8NiKclwArdC', 'Snx8t7sc_wT0VU8jac0NJ', '7Karhukm8I4uL8lSks19u', 'aw6FE0lUdSwFLs1onqucp', 'YF9TGV_MWG-qBg6EwGkx-', 'V9B7dwRIpyDCjYDegSOdL', 'SB8_tvoEGBnUfREgic7Al', 'LOAQtIjcRmYsCmuXclpxp', 'lYQHGSQL8tqUaK9Ex0omx', 'TjZcq1xx_oMduV4hLIi19', 'nE0_BITSwmRTVCj9EwSRs', 'oTlVPWW2h8APtkZVXKRpZ'}
reason = "remove_delete_steps_recheck_skip_end_modify_title_remove_is_remake_remove_validation_remove_redo_parent"
total_instr = set()
for json_path in json_paths:
    m_json_path = json_path.parent.parent/f"{reason}_{str(int(time.time()/100))}"/json_path.name
    os.makedirs(m_json_path.parent, exist_ok=True)
    modified_data = []
    with open(json_path, 'r') as f:
        data = json.load(f)
    for d in data:
        flow_ins = WebAgentFlow(d)
        if flow_ins.id in skip_ids:

            continue
        if flow_ins.id in total_instr:
            continue
        if 'validation' in flow_ins._flow_dict:
            del flow_ins._flow_dict['validation']
        skip_flow = False
        new_steps = []
        for step in flow_ins.steps:
            if '[is_remake]' in step.title and not '[not_is_remake]' in step.title:
                skip_flow = True
            if step.deleted or step.deleted_by_qc and step.title.lower() not in ['end']:
                logger.info(f"step: {step.id} removed")
            else:
                # if any(i in step.title for i in ['[is_remake]', '[not_is_remake]', '[REMOVED]', '[NOT_REMOVED]'])
                new_steps.append(step)
        if skip_flow:
            logger.error(f"{flow_ins.id} skipped.")
            continue
        flow_ins._steps = new_steps
        flow_ins._flow_dict['steps'] = [i.to_dict() for i in flow_ins._steps]
        modified_data.append(flow_ins.to_dict())
        total_instr.add(flow_ins.id)
    chunk_size = 30
    # 拆分成多个小文件
    for i in range(0, len(modified_data), chunk_size):
        chunk = modified_data[i:i + chunk_size]
        chunk_index = i // chunk_size + 1
        output_path = m_json_path.parent/str(m_json_path.stem+f'_part_{chunk_index}.json')
        with open(output_path, 'w', encoding='utf-8') as out_f:
            json.dump(chunk, out_f, ensure_ascii=False, indent=2)
        print(f'Saved: {output_path}')
    # with open(m_json_path, 'w') as f:
    #     json.dump(modified_data, f, indent=4, ensure_ascii=False)

# for json_path in d_json_paths:
#     with open(json_path, 'r') as f:
#         data = json.load(f)
#     for d in data:
#         flow_ins2 = WebAgentFlow(d)
#         if flow_ins2.id not in total_instr and flow_ins2.id not in skip_ids:
#             logger.error(f"{flow_ins2.id}: {json_path.name}")
logger.success(f"Total: {len(total_instr)}")