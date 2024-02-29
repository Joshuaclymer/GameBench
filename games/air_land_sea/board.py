@dataclass
class Board:
    order: List[Theater] # length 3
    def rotate_theater(self, theater_id: str):
        # rotate the theaters clockwise
        pass
    def get_board_string(self):
        # return a string representation of the board
        pass
    def get_theater(self, theater_id: str):
        # return the theater with the given id
        pass

@dataclass
class Theater:
    theater_id: str
    player_1_total_strength: int
    player_2_total_strength: int
    def get_theater_string(self):
        # return a string representation of the theater
        pass
    def get_strength(self, player_id: int):
        # return the strength of the player in the theater
        pass