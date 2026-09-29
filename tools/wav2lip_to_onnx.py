"""Convert an original Wav2Lip PyTorch checkpoint (wav2lip_gan.pth) to ONNX.

Only needed if the ONNX download mirrors are unavailable. Requires PyTorch:
    pip install torch --index-url https://download.pytorch.org/whl/cpu
    python tools/wav2lip_to_onnx.py path/to/wav2lip_gan.pth models/wav2lip_gan.onnx
"""
import sys

import torch
from torch import nn


class Conv2d(nn.Module):
    def __init__(self, cin, cout, kernel_size, stride, padding, residual=False):
        super().__init__()
        self.conv_block = nn.Sequential(nn.Conv2d(cin, cout, kernel_size, stride, padding),
                                        nn.BatchNorm2d(cout))
        self.act = nn.ReLU()
        self.residual = residual

    def forward(self, x):
        out = self.conv_block(x)
        if self.residual:
            out = out + x
        return self.act(out)


class Conv2dTranspose(nn.Module):
    def __init__(self, cin, cout, kernel_size, stride, padding, output_padding=0):
        super().__init__()
        self.conv_block = nn.Sequential(
            nn.ConvTranspose2d(cin, cout, kernel_size, stride, padding, output_padding),
            nn.BatchNorm2d(cout))
        self.act = nn.ReLU()

    def forward(self, x):
        return self.act(self.conv_block(x))


def _res(c):
    return Conv2d(c, c, 3, 1, 1, residual=True)


class Wav2Lip(nn.Module):
    def __init__(self):
        super().__init__()
        self.face_encoder_blocks = nn.ModuleList([
            nn.Sequential(Conv2d(6, 16, 7, 1, 3)),
            nn.Sequential(Conv2d(16, 32, 3, 2, 1), _res(32), _res(32)),
            nn.Sequential(Conv2d(32, 64, 3, 2, 1), _res(64), _res(64), _res(64)),
            nn.Sequential(Conv2d(64, 128, 3, 2, 1), _res(128), _res(128)),
            nn.Sequential(Conv2d(128, 256, 3, 2, 1), _res(256), _res(256)),
            nn.Sequential(Conv2d(256, 512, 3, 2, 1), _res(512)),
            nn.Sequential(Conv2d(512, 512, 3, 1, 0), Conv2d(512, 512, 1, 1, 0)),
        ])
        self.audio_encoder = nn.Sequential(
            Conv2d(1, 32, 3, 1, 1), _res(32), _res(32),
            Conv2d(32, 64, 3, (3, 1), 1), _res(64), _res(64),
            Conv2d(64, 128, 3, 3, 1), _res(128), _res(128),
            Conv2d(128, 256, 3, (3, 2), 1), _res(256),
            Conv2d(256, 512, 3, 1, 0), Conv2d(512, 512, 1, 1, 0),
        )
        self.face_decoder_blocks = nn.ModuleList([
            nn.Sequential(Conv2d(512, 512, 1, 1, 0)),
            nn.Sequential(Conv2dTranspose(1024, 512, 3, 1, 0), _res(512)),
            nn.Sequential(Conv2dTranspose(1024, 512, 3, 2, 1, 1), _res(512), _res(512)),
            nn.Sequential(Conv2dTranspose(768, 384, 3, 2, 1, 1), _res(384), _res(384)),
            nn.Sequential(Conv2dTranspose(512, 256, 3, 2, 1, 1), _res(256), _res(256)),
            nn.Sequential(Conv2dTranspose(320, 128, 3, 2, 1, 1), _res(128), _res(128)),
            nn.Sequential(Conv2dTranspose(160, 64, 3, 2, 1, 1), _res(64), _res(64)),
        ])
        self.output_block = nn.Sequential(Conv2d(80, 32, 3, 1, 1),
                                          nn.Conv2d(32, 3, 1, 1, 0), nn.Sigmoid())

    def forward(self, audio_sequences, face_sequences):
        audio_embedding = self.audio_encoder(audio_sequences)
        feats = []
        x = face_sequences
        for f in self.face_encoder_blocks:
            x = f(x)
            feats.append(x)
        x = audio_embedding
        for f in self.face_decoder_blocks:
            x = f(x)
            x = torch.cat((x, feats[-1]), dim=1)
            feats.pop()
        return self.output_block(x)


def export(model, dst):
    model.eval()
    mel = torch.zeros(1, 1, 80, 16)
    face = torch.zeros(1, 6, 96, 96)
    kwargs = dict(input_names=["source", "target"], output_names=["output"], opset_version=13,
                  dynamic_axes={"source": {0: "batch"}, "target": {0: "batch"},
                                "output": {0: "batch"}})
    try:  # classic exporter: one self-contained .onnx file
        torch.onnx.export(model, (mel, face), dst, dynamo=False, **kwargs)
    except TypeError:  # older PyTorch without the `dynamo` switch
        torch.onnx.export(model, (mel, face), dst, **kwargs)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    ckpt = torch.load(sys.argv[1], map_location="cpu")
    state = ckpt.get("state_dict", ckpt)
    state = {k.replace("module.", "", 1): v for k, v in state.items()}
    model = Wav2Lip()
    model.load_state_dict(state)
    export(model, sys.argv[2])
    print("Saved", sys.argv[2])


if __name__ == "__main__":
    main()
