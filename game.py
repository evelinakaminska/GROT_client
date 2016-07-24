"""
Play GROT game.
"""

import http.client
import json
import random
import time
import pprint
import math
from copy import deepcopy
board_size = 5
#threshold = 250

def icon(direction):
    sign = 'o'
    
    if direction == 'up':
        sign = '^'
    elif direction == 'down':
        sign = 'v'
    elif direction == 'left':
        sign = '<'
    elif direction == 'right':
        sign = '>'
    
    print(sign, end='')
    

def show(board):
    for row in board:
        for point in row:
            icon(point['direction'])
        print()
    print()

def calc_points(board) :
    #pp=pprint.PrettyPrinter(indent=4)
    #pp.pprint(board)
    score = 0
    cols = [None for i in range(board_size)]
    raws = [None for i in range(board_size)]
    for y in range(board_size) :
        for x in range(board_size) :
            if board[y][x]["direction"] == None :
                score += board[y][x]["points"]
            else :
                cols[x] = 1
                raws[y] = 1
    for i in raws :
        if i == None :
            score += 10*(board_size)
    for i in cols :
        if i == None :
            score += 10*(board_size)
    return score            

def calc_next_point(point, board):
    current_board = deepcopy(board)
    if point["direction"] == "up" :
        if point["y"] == 0 :
            return None
        else : 
            next_point = current_board[point["y"]-1][point["x"]]
    elif point["direction"] == "down" :
        if point["y"] == board_size-1 :
            return None
        else :
            next_point = current_board[point["y"]+1][point["x"]]
    elif point["direction"] == "left" :
        if point["x"] == 0 :
            return None
        else :
            next_point = current_board[point["y"]][point["x"]-1]
    elif point["direction"] == "right" :
        if point["x"] == board_size-1 :
            return None
        else :
            next_point = current_board[point["y"]][point["x"]+1]

    if next_point["direction"] == None : 
        current_board[point["y"]][point["x"]]["direction"] = None
        current_board[next_point["y"]][next_point["x"]]["direction"] = point["direction"]
        next_point["direction"] = point["direction"]
        return calc_next_point(next_point, current_board)
    else :
        return next_point

def move(point, board, score, moves):
    temp_board = deepcopy(board)
    #score += point["points"]
    moves += 1
    next_point = calc_next_point(point, temp_board)
    temp_board[point["y"]][point["x"]]["direction"] = None
    #print (point, moves)
    #show(temp_board)
    if next_point == None :
        score += calc_points(temp_board)
        #print (0, score, moves, point)
        return (score, moves)
    else :
        return move(next_point, temp_board, score, moves)

def get_move(data):
    """
    Get coordinates (start point) of next move.
    """
    board = deepcopy(data["board"])
    #pp=pprint.PrettyPrinter(indent=4)
    #pp.pprint(board)

    best_point = {
        'x': 0,
        'y': 0,
    }
    best_result = (0, 0)
    # result = (score, moves)
    for x in range(board_size) :
        for y in range(board_size) :
            temp_result = move(board[y][x], board, 0, 0)
            #threshold = math.floor(data["score"] / (5*board_size*board_size)) + board_size - 1
            threshold = 300
            if ((data["score"] > threshold) and (temp_result[0] > best_result[0])) or ((data["score"] <= threshold) and (temp_result[1] > best_result[1])) :
            #if ((temp_result[1] > threshold) and (temp_result[1] > best_result[1])) or ((temp_result[1] >= best_result[1]) and (temp_result[0] > best_result[0])) :
                best_result = temp_result
                best_point = {
                    'x': x,
                    'y': y,
                }

    #print (data["score"],best_result)
    #print (best_point)
    return best_point

def play(room_id, token, server, debug=False, alias=''):
    """
    Connect to game server and play rounds in the loop until end of game.
    """
    # connect to the game server
    client = http.client.HTTPConnection(server)
    client.connect()
    game_url = '/games/{}/board?token={}'.format(room_id, token)
    if alias:
        game_url += '&alias={}'.format(alias)

    # wait until the game starts
    client.request('GET', game_url)

    response = client.getresponse()

    while response.status == 200:
        data = json.loads(response.read().decode())
        #debug = True
        if debug:
            #print(data)
            pp=pprint.PrettyPrinter(indent=4)
            pp.pprint(data)
            # sleep 3 seconds so, you will be able to read printed data
            time.sleep(3)

        # make your move and wait for a new round
        client.request('POST', game_url, json.dumps(get_move(data)))

        response = client.getresponse()
