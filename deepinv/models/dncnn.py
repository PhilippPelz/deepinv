import torch.nn as nn
from .denoiser import register

@register('dncnn')
class DnCNN(nn.Module):
    def __init__(self, in_channels=1, out_channels=1, depth=20, act_mode='R', bias=True, nf=64, pretrain=False, ckpt_path=None, train=False,  device=None):
        """
        TODO: add doc
        """
        super(DnCNN, self).__init__()

        self.depth = depth

        self.in_conv = nn.Conv2d(in_channels, nf, kernel_size=3, stride=1, padding=1, bias=bias)
        self.conv_list = nn.ModuleList(
            [nn.Conv2d(nf, nf, kernel_size=3, stride=1, padding=1, bias=bias) for _ in range(self.depth - 2)])
        self.out_conv = nn.Conv2d(nf, out_channels, kernel_size=3, stride=1, padding=1, bias=bias)

        if act_mode == 'R':  # Kai Zhang's nomenclature
            self.nl_list = nn.ModuleList([nn.ReLU() for _ in range(self.depth - 1)])

        if pretrain and ckpt_path is not None:
            self.load_state_dict(torch.load(ckpt_path, map_location=lambda storage, loc: storage), strict=True)

        if not train:
            self.eval()
            for _, v in self.named_parameters():
                v.requires_grad = False

        if device is not None:
            self.to(device)

    def forward(self, x_in, denoise_level=None):

        x = self.in_conv(x_in)
        x = self.nl_list[0](x)

        for i in range(self.depth - 2):
            x_l = self.conv_list[i](x)
            x = self.nl_list[i + 1](x_l)

        return self.out_conv(x) + x_in