import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.nn.init as init
from .Utils import *
class STN(nn.Module):
    def __init__(self):
        super(STN, self).__init__()
        

        self.localization = nn.Sequential(
            nn.Conv2d(3, 32, kernel_size=(7, 7), stride=(2, 2), padding=(1, 1), bias=False),
            nn.BatchNorm2d(32, eps=0.0001, momentum=0.1, affine=True,track_running_stats=True),
            nn.ReLU(),
            nn.Conv2d(32, 80, kernel_size=(5, 5), stride=(2, 2), padding=(1, 1), bias=False),
            nn.BatchNorm2d(80, eps=0.0001, momentum=0.1, affine=True, track_running_stats=True),
            nn.ReLU(),
            nn.Conv2d(80, 64, kernel_size=(3, 3), stride=(2, 2), padding=(1, 1), bias=False),
            nn.BatchNorm2d(64, eps=0.0001, momentum=0.1, affine=True, track_running_stats=True),
            nn.MaxPool2d(2, stride=2),
            nn.ReLU()
        )

        self.fc_loc = nn.Sequential(
            nn.Linear(64*13*13, 128),
            nn.ReLU(True),
            nn.Linear(128, 3 * 2)
        )
        self.initialize_weights()
        
    def initialize_weights(self):
        for m in self.localization.modules():
            if isinstance(m, nn.Conv2d):
                init.kaiming_normal_(m.weight, nonlinearity='relu')
            elif isinstance(m, nn.BatchNorm2d):
                init.constant_(m.weight, 1)
                init.constant_(m.bias, 0)

        for m in self.fc_loc.modules():
            if isinstance(m, nn.Linear):
                init.kaiming_normal_(m.weight, nonlinearity='relu')
                init.constant_(m.bias, 0)
        
        self.fc_loc[2].weight.data.zero_()
        self.fc_loc[2].bias.data.copy_(torch.tensor([1, 0, 0, 0, 1, 0], dtype=torch.float))

    def forward(self, x):
        B, C, H, W = x.shape
        xs = self.localization(x)
        xs = xs.view(B, -1)
        theta = self.fc_loc(xs)
        theta = theta.view(B, 2, 3)

        grid = F.affine_grid(theta, x.size(), align_corners=True)
        x = F.grid_sample(x, grid, align_corners=True)

        return x
    
if __name__ == "__main__":
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    stn = STN().to(device)
    print_total_params(stn)
    x = torch.randn(8, 3, 224, 224).to(device)

    transformed_x = stn(x)
    print(f"Input shape: {x.shape}")
    print(f"Output shape: {transformed_x.shape}")