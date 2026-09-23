import torch
import torch.nn as nn


class ParkingStateClassifier(nn.Module):
    """
    Binary classifier for parking state: parked (1) vs moving (0).
    
    Input: 3 sensor features (gps_speed, ble_rssi, imu_magnitude)
    Output: Probability of being parked (sigmoid output, 0-1)
    """
    
    def __init__(self, input_size: int = 3, hidden1: int = 16, hidden2: int = 8):
        super().__init__()
        self.fc1 = nn.Linear(input_size, hidden1)
        self.relu1 = nn.ReLU()
        self.fc2 = nn.Linear(hidden1, hidden2)
        self.relu2 = nn.ReLU()
        self.fc3 = nn.Linear(hidden2, 1)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through the network.
        
        Args:
            x: Tensor of shape (batch_size, 3) with features [gps_speed, ble_rssi, imu_magnitude]
        
        Returns:
            Logits of shape (batch_size, 1) (before sigmoid, for use with BCEWithLogitsLoss)
        """
        x = self.relu1(self.fc1(x))
        x = self.relu2(self.fc2(x))
        x = self.fc3(x)
        return x
    
    def predict_proba(self, x: torch.Tensor) -> torch.Tensor:
        """Get probabilities (with sigmoid applied)."""
        with torch.no_grad():
            logits = self.forward(x)
            return torch.sigmoid(logits)
