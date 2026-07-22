import numpy as np


def preprocess(signals: dict):
    """
    Devuelve (1, 128, 9)
    Orden:
    ankle_x, ankle_y, ankle_z,
    thigh_x, thigh_y, thigh_z,
    hip_x, hip_y, hip_z
    """

    X = []

    for sensor in ["ankle", "thigh", "hip"]:
        X.append(signals[sensor]["x"])
        X.append(signals[sensor]["y"])
        X.append(signals[sensor]["z"])

    X = np.array(X).T
    X = X[np.newaxis, :, :]

    return X.astype(np.float32)
