import numpy as np
from pandas import DataFrame, Series


def get_velocity(track_df: DataFrame) -> np.array:
    """
    Calculates velocity given x-velocity and y-velocity

    :param track_df: track data frame of a vehicle
    :return: array of velocities for vehicle
    """
    return np.sqrt(track_df.xVelocity**2 + track_df.yVelocity**2)


def get_orientation(track_df: DataFrame) -> np.array:
    """
    Calculates orientation given x-velocity and y-velocity

    :param track_df: track data frame of a vehicle
    :return: array of orientations for vehicle
    """
    return np.arctan2(-track_df.yVelocity, track_df.xVelocity)


def get_acceleration(track_df: DataFrame, orientation: np.array) -> np.array:
    """
    Calculates acceleration given x-acceleration and y-acceleration

    :param track_df: track data frame of a vehicle
    :return: array of accelerations for vehicle
    """
    return np.cos(orientation) * track_df.xAcceleration + np.sin(orientation) * (
        -track_df.yAcceleration
    )


def get_dt(recording_df: DataFrame) -> float:
    """
    Extracts time step size from data frame

    :param recording_df: data frame of the recording meta information
    :return: time step size
    """
    return float(1.0 / recording_df["frameRate"].iloc[0])

def unwrap_track_orientations(
    vehicle_tracks: DataFrame,
    speed_epsilon: float = 0.2,
) -> Series:
    orientations = vehicle_tracks["orientation"].copy()

    for vehicle_id, track in vehicle_tracks.groupby("id", sort=False):
        track = track.sort_values("frame")
        index = track.index

        theta = track["orientation"].to_numpy(dtype=float)
        speed = track["velocity"].to_numpy(dtype=float)

        valid = np.isfinite(theta) & np.isfinite(speed) & (speed >= speed_epsilon)

        if not np.any(valid):
            continue

        fixed = theta.copy()

        # For nearly stationary frames, heading is undefined. Carry the nearest
        # valid heading through those samples before unwrapping, so zero-speed
        # velocity noise cannot create artificial rotations.
        valid_indices = np.flatnonzero(valid)
        first_valid = valid_indices[0]
        fixed[:first_valid] = fixed[first_valid]

        last_valid = first_valid
        for i in range(first_valid + 1, len(fixed)):
            if valid[i]:
                last_valid = i
            else:
                fixed[i] = fixed[last_valid]

        fixed = np.unwrap(fixed)
        orientations.loc[index] = fixed

    return orientations
