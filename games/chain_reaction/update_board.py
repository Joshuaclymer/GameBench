## iterative Aish

def update_board(board_state, action, player_id):
    """Updates the board in a game of chain reaction, handling explosions, chain reactions, orb placement, and validity checks.

    Args:
        board_state: A list of lists representing the current board state.
        action: A tuple (row, col) indicating the cell where the player placed an orb.
        player_id: The ID of the player who placed the orb.

    Returns:
        The updated board state after handling explosions, chain reactions, and orb placement.
    """

    rows = len(board_state)
    cols = len(board_state[0])

    row, col = action

    available_actions = []

    for r in range(rows):
        for c in range(cols):
            cell_state = board_state[r][c]
            # Check if the cell is empty or has orbs of the player's color
            if cell_state == '--' or cell_state[0] == str(player_id):
                available_actions.append((r,c))

    def get_critical_mass(row, col):
        """
        Get the critical mass for a given cell.

        Parameters:
        - row (int): Row index of the cell.
        - col (int): Column index of the cell.

        Returns:
        - int: Critical mass for the cell.
        """
        if row == 0 or row == rows - 1:
            if col == 0 or col == cols - 1:
                return 2  # Corner cell
            return 3  # Edge cell
        if col == 0 or col == cols - 1:
            return 3  # Edge cell
        return 4  # Interior cell

    def explode(board_state, row, col): ## to be called only when the cell is over critical mass
        """Handles the explosion of a cell and its surrounding cells iteratively,
        checking only orthogonally neighboring cells for potential chain reactions
        until none remain.

        Adds orbs to orthogonally adjacent cells, regardless of player ownership,
        and tracks updated cells to avoid redundant processing.
        """

        player_id = board_state[row][col][0]
        critical_mass = int(board_state[row][col][1])

        rows = len(board_state)
        cols = len(board_state[0])

        # Make a list of neighnours to update
        orthogonal_neighbours = []

        if critical_mass == 2:
            if row == 0:
                orthogonal_neighbours.append((row+1,col))
                if col == 0:
                    orthogonal_neighbours.append((row,col+1))
                else:
                    orthogonal_neighbours.append((row,col-1))
            if row == row-1:
                orthogonal_neighbours.append((row-1,col))
                if col == cols-1:
                    orthogonal_neighbours.append((row,col-1))
                else:
                    orthogonal_neighbours.append((row,col+1))

        if critical_mass == 3:
            if row == 0:
                orthogonal_neighbours += [(row,col-1),(row+1,col),(row,col+1)]
            elif row == rows-1:
                orthogonal_neighbours += [(row,col-1),(row-1,col),(row,col+1)]
            elif col == 0:
                orthogonal_neighbours += [(row-1,col),(row,col+1),(row+1,col)]
            else:
                orthogonal_neighbours += [(row-1,col),(row,col-1),(row+1,col)]

        if critical_mass == 4:
            orthogonal_neighbours += [(row-1,col),(row+1,col),(row,col-1),(row,col+1)]

        # Empty the exploded cell
        print('Emptied cell:',row,col)
        board_state[row][col] = "--"

        # Initialize list of cells that are unstable because of the explosion
        unstable_cells = []

        # Add 1 orb to neighbouring cells regardless of ownership
        for cntr, (r,c) in enumerate(orthogonal_neighbours):
            print('Updating cell:',r,c)
            if board_state[r][c][1] == '-':
                num_orbs = 1
                print('Just 1 orb')
                print('Updated board')
            else:
                num_orbs = int(board_state[r][c][1]) + 1
                if num_orbs >= get_critical_mass(r, c):
                    unstable_cells.append((r, c))
                    print('Unstable cells:',unstable_cells)

            # Update player ID and number of orbs
            board_state[r][c] = f"{player_id}{num_orbs}"
            print('Updated board!')
            print('Unstable cells:', unstable_cells)

            print('-----------------')
            for row in board_state:
                print(row)
            print('-----------------')

        return board_state, unstable_cells

    # Check for valid action
    if not (0 <= row < len(board_state) and 0 <= col < len(board_state[0])):
        action = random.choice(available_actions)
        row, col = action
        print("Action outside board boundaries, selecting random legal action:",action)
    if board_state[row][col][0] != "-" and board_state[row][col][0] != player_id:
        action = random.choice(available_actions)
        row, col = action
        print("Cannot place orb in opponent's cell, selecting random legal action:",action)

    if board_state[row][col][0] == player_id:  # Player already has an orb in this cell
        num_orbs = int(board_state[row][col][1]) + 1
        board_state[row][col] = f"{player_id}{num_orbs}"
    else:  # Place the first orb
        board_state[row][col] = f"{player_id}1"

    critical_mass = get_critical_mass(row, col)
    if int(board_state[row][col][1]) >= critical_mass:
        print('Calling explosion on:',row,col)
        board_state, unstable_cells = explode(board_state, row, col)  # Trigger explosion and chain reactions
    else:
        unstable_cells = []

    # Call the explode function on cells which are unstable
    while len(unstable_cells)>0:
        for cntru, (ru,cu) in enumerate(unstable_cells):
            print('Calling recursive explosion on:',ru,cu)
            board_state, unstable_cells = explode(board_state,ru,cu)

    return board_state
