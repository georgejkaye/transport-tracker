from dataclasses import dataclass

from api.stats.classes.train import UserTrainAllStats


@dataclass
class UserDetails:
    user_id: int
    user_name: str
    display_name: str
    train_stats: UserTrainAllStats
