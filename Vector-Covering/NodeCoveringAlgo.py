# Fix various flickering issues
# Account for line losses, done as a loss per unit distance. --> Implies that the quantities and etc must be changed. --> We aim
# ,,, for the most accurate matching

import pygame, math, time, random, copy, sys, signal
from pygame.locals import *
from collections import OrderedDict


# MARK: Error Handling
class timeoutException(Exception):
    pass


# MARK: Requirements pertaining to building pygame interface
WIDTH = 1000
HEIGHT = 600
SCALE = 60

RED = (255,0,0)
BLUE = (0,0,255)
GREEN = (0,255,0)
WHITE = (255,255,255)
BLACK = (0,0,0)
ORANGE = (255,165,0)
PINK = (255,153,153)

pygame.init()

ICON = pygame.image.load('Auxo_Logo_Black.png')

DISPLAYSURF = pygame.display.set_mode((WIDTH, HEIGHT))
FONT = pygame.font.SysFont("Arial", 18)
pygame.display.set_caption("Project Auxo Network, v8")
pygame.display.set_icon(ICON)

BACKGROUND = pygame.Surface(DISPLAYSURF.get_size())
BACKGROUND = BACKGROUND.convert()
BACKGROUND.fill(BLACK)


# MARK: Classes for the network elements
class Node:
    def __init__(self, name, pos, quantity):
        self.name = str(name)
        self.x, self.y = pos
        self.color = RED
        self.circle_rect = None
        self.quantity = quantity

    def draw(self):
        self.circle_rect = pygame.draw.circle(DISPLAYSURF, self.color, (self.x, self.y), 5)
        pygame.draw.circle(DISPLAYSURF, self.color, (self.x,self.y), 5)
        DISPLAYSURF.blit(FONT.render(self.name, True, GREEN),(self.x,self.y))

    def change_color(self, color):
        self.color = color


class Edge:
    def __init__(self, label, start_end): # type(start_end) is tuple
        self.label = str(label)
        self.start, self.end = start_end
        self.length = int(self.get_length())
        self.color = RED

    def draw(self):
        mid_x = (self.start[0] + self.end[0])/2
        mid_y = (self.start[1] + self.end[1])/2
        pygame.draw.line(DISPLAYSURF, self.color, self.start, self.end)
        DISPLAYSURF.blit(FONT.render(str(self.length), True, WHITE), (mid_x, mid_y))

    def change_color(self, color):
        self.color = color

    def get_length(self):
        x_1, y_1 = self.start
        x_2, y_2 = self.end
        return "%.0f" % math.hypot(x_1 - x_2, y_1 - y_2)


class LeadVec:
    def __init__(self, s_node, e_node):
        self.s_node = s_node
        self.e_node = e_node

    def draw(self):
        pygame.draw.line(DISPLAYSURF, BLUE, (self.s_node.x, self.s_node.y), (self.e_node.x, self.e_node.y), 5)

    def length(self):
        return Edge("Lead_Vec", ((self.s_node.x, self.s_node.y), (self.e_node.x, self.e_node.y))).length


# MARK: Variables concerning the algorithms
QUANTITY_RANGE = 20


# MARK: Network requirements
node_dict = {}
buyer_dict = {}
seller_dict = {}
edge_dict = {}
network_graph = {}

node_pos = {0 : (10,10),
            1 : (200,200),
            2 : (100,100),
            3 : (350,80),
            4 : (190,30),
            5 : (300,20),
            6 : (130,300),
            7 : (50,200),
            8 : (958,54),
            9 : (298,434),
            10 : (340,275),
            11 : (57,264),
            12 : (354,332),
            13 : (525,232),
            14 : (601,526),
            15 : (749,442),
            16 : (926,371)
}

edges_list = """
1:2 1:3 2:4 1:4 3:4 3:5 2:6 6:1 4:5 7:2 7:0 7:11 13:10
12:1 1:10 3:13 13:9 13:14 9:14 13:15 8:16 5:8 16:15 0:2
"""
edges_list = [x.split(':') for x in edges_list.split()]


# MARK: Building the network
for nodal_el in node_pos:
    if nodal_el is 0:
        node_dict[nodal_el] = Node(nodal_el, node_pos[nodal_el], 1000)
        seller_dict[nodal_el] = node_dict[nodal_el]
    else:
        node_dict[nodal_el] = Node(nodal_el, node_pos[nodal_el],
                                   random.randrange(-QUANTITY_RANGE, QUANTITY_RANGE))

        # Filter to buyer and seller
        if node_dict[nodal_el].quantity > 0:
            seller_dict[int(node_dict[nodal_el].name)] = node_dict[nodal_el]
        elif node_dict[nodal_el].quantity < 0:
            buyer_dict[int(node_dict[nodal_el].name)] = node_dict[nodal_el]
        else:
            pass

for edge_el in edges_list:
    edge_el = tuple(edge_el)
    edge_dict[edge_el] = Edge(edge_el, (node_pos[int(edge_el[0])], node_pos[int(edge_el[1])]))

for node_name in node_dict:
    network_graph[node_name] = []

for edge_name in edges_list:
    edge_f = int(edge_name[0])
    edge_i = int(edge_name[1])
    network_graph.setdefault(edge_i, list()).append(edge_f)
    network_graph[edge_f].append(edge_i)


# MARK: Functions concerning network navigation
def find_path(start_node, end_node):
    prev_child = start_node
    current_node = start_node
    path = []
    visited_nodes = []
    to_delete_nodes = []

    path.append(start_node)
    visited_nodes.append(start_node)

    if start_node not in network_graph or end_node not in network_graph:
        return None

    while current_node != end_node:
        lead_lengths = {}

        if len(network_graph[current_node]) > 0:
            # --> find leadvec distances from each c_node
            for c_node in network_graph[current_node]:
                if c_node not in visited_nodes:
                    lead_lengths[c_node] = LeadVec(node_dict[c_node], node_dict[end_node]).length()

                    # To draw the vectors
                    '''
                    lead_vec = LeadVec(node_dict[c_node], node_dict[end_node])
                    lead_vec.draw()
                    lead_lengths[c_node] = lead_vec.length()
                    '''
            try:
                new_child = min(lead_lengths, key=lead_lengths.get)
            except:
                new_child = prev_child

            # --> If already visited
            start_time = time.time()
            while new_child in visited_nodes:
                # --> Time out exception
                if time.time() - start_time > 2:
                    raise timeoutException

                lead_lengths.clear()
                visited_nodes.append(new_child)
                to_delete_nodes.append(current_node)

                for c_node in network_graph[new_child]:
                    if c_node not in visited_nodes:
                        lead_lengths[c_node] = LeadVec(node_dict[c_node], node_dict[end_node]).length()


                if len(lead_lengths) > 0:
                    new_child = min(lead_lengths, key=lead_lengths.get)
                else:
                    new_child = prev_child



            visited_nodes.append(new_child)
            path.append(new_child)
            path = list(OrderedDict.fromkeys(path))

            prev_child = current_node
            current_node = new_child

        # --> This means that our current node has no connection, go back
        else:
            visited_nodes.append(current_node)
            current_node = prev_child

    # --> Filter the list to get rid of all corresponding to_delete_nodes
    return [x for x in path if x not in to_delete_nodes]


def determine_edges_c(path):
    # --> Finds the edges for the node list given
    connected_edges = []
    for x in range(1, len(path)):
        prev = str(path[x-1])
        second = str(path[x])
        pair = (prev,second)
        r_pair = (second, prev)
        if pair != r_pair:
            connected_edges.append(pair)
            connected_edges.append(r_pair)
    return connected_edges


def path_distance(edge_list):
    distance_list = []
    for element in edge_list:
        if element in edge_dict:
            distance_list.append(edge_dict[element].length)
    return sum(distance_list)


def find_shortest_path(start_node, end_node):
    try:
        path = find_path(start_node, end_node)
        r_path = find_path(end_node, start_node)
        dis = path_distance(determine_edges_c(path))
        r_dis = path_distance(determine_edges_c(r_path))
        if r_dis < dis:
            return r_path[::-1] # We reverse the path because it's been backward checked
        return path
    except timeoutException:
        r_path = find_path(end_node, start_node)
        return r_path[::-1]


# MARK: Functions pertaining to the Matching Mechanism
def match_market(buyer_node, seller_dict):
    # --> Returns a dictionary of the matches for a buyer node
    match_dict = {}
    b_name = buyer_node.name
    for seller in seller_dict:
        pair_name = b_name + "," + seller_dict[seller].name
        quantity_diff = buyer_node.quantity + seller_dict[seller].quantity
        match_dict[pair_name] = quantity_diff

    return match_dict


def find_best(buyer_node, Rseller_dict):
    # --> Returns the best sellers (list) for buyer to be matched
    pairings = []
    buyer_node_copy = copy.deepcopy(buyer_node)

    while buyer_node_copy.quantity != 0:

        quantity_list = []
        matches_dict = match_market(buyer_node_copy, Rseller_dict)

        if len(matches_dict) > 0:
            for item in matches_dict:
                if buyer_node_copy.name == item.split(',')[0]:
                    quantity_list.append(matches_dict[item])
        if len(quantity_list) > 0:
            smallest_q = min(quantity_list, key=abs)

        match_seller = -1
        for item in matches_dict:
            name = item.split(',')
            buyer_name = name[0]
            seller_name = name[1]
            if (buyer_node_copy.name == buyer_name) and matches_dict[item] == smallest_q:
                match_seller = seller_name
                break

        match_seller = int(match_seller)
        seller_Node = seller_dict[match_seller]
        quantity_s = seller_Node.quantity

        pairings.append(match_seller)


        if quantity_s > abs(buyer_node_copy.quantity):
            buyer_node_copy.quantity = 0
        elif quantity_s < abs(buyer_node_copy.quantity):
            Rseller_dict.pop(match_seller)
            buyer_node_copy.quantity += quantity_s
        else:
            buyer_node_copy.quantity = 0

    return pairings


def randomizeNodes(): # Whenever you want reset/randomize the node quantities

    seller_dict.clear()
    buyer_dict.clear()

    for element in node_pos:
        if element == 0:
            pass
        else:
            node_dict[element].quantity = random.randrange(-QUANTITY_RANGE,
                                                        QUANTITY_RANGE)  # Those with negative are buyers, those with positive sellers
            if node_dict[element].quantity > 0:
                seller_dict[int(node_dict[element].name)] = node_dict[element]
            elif node_dict[element].quantity == 0:
                pass
            else:
                buyer_dict[int(node_dict[element].name)] = node_dict[element]


# MARK: Functions that change the GUI
def draw_all_nodes(color):
    for el in node_pos:
        node_dict[el].change_color(color)
        node_dict[el].draw()


def draw_indv_node(color, node):
    node.change_color(color)
    node.draw()


def draw_indv_edge(color, edge):
    edge.change_color(color)
    edge.draw()


def text_objects(text, font):
    textSurface = font.render(text, True, WHITE)
    return textSurface, textSurface.get_rect()


def hover_display(text):
    text = "Quantity: {}".format(str(text))
    normText = pygame.font.Font('freesansbold.ttf', 20)
    TextSurf, TextRect = text_objects(text, normText)
    TextRect.center = ((SCALE),(HEIGHT - (SCALE-30)))
    DISPLAYSURF.blit(TextSurf, TextRect)

    pygame.display.update()
    time.sleep(0.1)
    DISPLAYSURF.fill(BLACK)


# MARK: Actual Opening of the GUI
if __name__ == "__main__":
    clock = pygame.time.Clock()
    DISPLAYSURF.blit(BACKGROUND, (0,0))

    # --> Variables that apply with pygame main loop
    hover = None
    mouse_click = False
    click_list = [0] * len(node_pos)

    draw_all_nodes(RED)

    for element in edges_list:
        element = tuple(element)
        edge_dict[element].draw()

    # --> Game loop
    while True:
        pair_list = []

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == MOUSEBUTTONDOWN:
                for indx, element in enumerate(node_pos):
                    mouse_click = node_dict[element].circle_rect.collidepoint(pygame.mouse.get_pos())
                    click_list[indx] = mouse_click

            elif event.type == KEYDOWN:
                if event.key == K_r:
                    randomizeNodes()
                if event.key == K_q:
                    pygame.quit()
                    sys.exit()

        # --> Hover and selection control
        for indx, element in enumerate(node_pos):
            hover = node_dict[element].circle_rect.collidepoint(pygame.mouse.get_pos())
            if hover:
                draw_indv_node(PINK, node_dict[element])
                hover_display(node_dict[element].quantity)



            elif click_list[indx] == 1: # --> Selection/click
                draw_indv_node(WHITE, node_dict[element])

                # --> Running the matching algorithms
                buyer_name = int(node_dict[element].name)

                if buyer_name in buyer_dict:
                    pair_list = find_best(buyer_dict[element], copy.deepcopy(seller_dict))

                    for pair in pair_list:
                        draw_indv_node(WHITE, node_dict[pair])

                        seller_name = int(pair)
                        path = find_shortest_path(buyer_name, seller_name)

                        edges_path = determine_edges_c(path)

                        for edge in edges_path:
                            try:
                                draw_indv_edge(WHITE, edge_dict[edge])
                            except:
                                draw_indv_edge(WHITE, edge_dict[edge[::-1]])

                    pygame.display.update()
                    time.sleep(0.1)

                else:
                    print "Confirm Buyer node, NOT seller"
                    pygame.display.update()

            else:
                # --> Default state
                draw_all_nodes(RED)
                for edge_obj in edge_dict:
                    draw_indv_edge(RED, edge_dict[edge_obj])

        pygame.display.update()
        clock.tick(60)
