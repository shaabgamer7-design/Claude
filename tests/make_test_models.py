"""Build stand-in models for offline testing (random-weight Wav2Lip with the
real architecture, identity "GFPGAN"). Real weights are downloaded by the app."""
import sys
from pathlib import Path

import numpy as np
import onnx
from onnx import TensorProto, helper

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))


def fake_gfpgan(dst):
    inp = helper.make_tensor_value_info("input", TensorProto.FLOAT, [1, 3, 512, 512])
    out = helper.make_tensor_value_info("output", TensorProto.FLOAT, [1, 3, 512, 512])
    # Unused padding weights so the file looks like a real model to the size check.
    pad = helper.make_tensor("pad", TensorProto.FLOAT, [8192], np.zeros(8192, np.float32))
    graph = helper.make_graph([helper.make_node("Identity", ["input"], ["output"])],
                              "fake_gfpgan", [inp], [out], initializer=[pad])
    model = helper.make_model(graph, opset_imports=[helper.make_opsetid("", 13)])
    model.ir_version = 8
    onnx.save(model, dst)


def random_wav2lip(dst):
    import torch
    from wav2lip_to_onnx import Wav2Lip, export
    torch.manual_seed(0)
    export(Wav2Lip(), dst)


if __name__ == "__main__":
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    random_wav2lip(str(out / "wav2lip_gan.onnx"))
    fake_gfpgan(str(out / "gfpgan_1.4.onnx"))
    print("ok")
