# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
#
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).


from captureAgents import CaptureAgent
import random, time, util, math
from game import Directions
import game
from util import nearestPoint
from game import Actions


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'SmartAgent', second = 'defensiveAgent'):
  """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.
  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

  # The following line is an example only; feel free to change it.
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """

  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    actions = gameState.getLegalActions(self.index)

    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    foodLeft = len(self.getFood(gameState).asList())

    if foodLeft <= 2:
      bestDist = 9999
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        pos2 = successor.getAgentPosition(self.index)
        dist = self.getMazeDistance(self.start, pos2)
        if dist < bestDist:
          bestAction = action
          bestDist = dist
      return bestAction

    return random.choice(bestActions)

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)
    return features * weights

  def getFeatures(self, gameState, action):
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}

class SmartAgent(CaptureAgent):
  """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

  def registerInitialState(self, gameState):
    """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).
    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)
    IMPORTANT: This method may run for at most 15 seconds.
    """

    '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
    CaptureAgent.registerInitialState(self, gameState)
    self.start = gameState.getAgentPosition(self.index)
    self.state = gameState
    self.width = gameState.data.layout.width
    self.height = gameState.data.layout.height
    self.homeBoarder = self.getHomeBorader(self.state)
    self.enemyBoarder = self.getEnemyBorader(self.state)
    self.homeTerritory = self.getHomeTerritory()
    self.enemyTerritory = self.getEnemyTerritory()
    self.memberID = self.getMemberID(gameState)
    self.numWander = 0
    self.isInGate = False
    self.gatePos = None
    self.safePos = None
    self.attackPoint = None
    self.isChangedAttackPoint = False
    self.queue = util.Queue()
    self.escapeState = False
    self.cost = 0
    self.goHomePath = []
    self.isDodging = False
    self.opponents = self.getOpponents(gameState)
    self.defendingCapsule = self.getCapsulesYouAreDefending(gameState)
    self.homeBorder = getHomeBorder(gameState, self.red)
    self.homeBorderWithoutCorner = self.getHomeBoarderWithoutCorner(gameState)
    self.defensePath = []
    self.time = 0
    self.MazegoalPos = random.choice(self.homeBorderWithoutCorner)  #new add
    self.canReverse = True
    self.lastPosition = None
    '''
    Your initialization code goes here, if you need any.
    '''
  # def manhattan(self, pos1, pos2):
  #   x1, y1 = pos1; x2, y2 = pos2
  #   return abs(x1 - x2) + abs(y1 - y2)

  def greedyHeuristic(self, pos, foodlist):
    """
    Given a position and food list, calculate minimal spanning
    tree distance from that position to n - 2 food dots, where
    n = len(foodlist).
    """
    if len(foodlist) < 2:
      return 0
    next_foodlist = foodlist.copy()
    min_food = None
    min_dis = float('inf')
    for food in foodlist:
      dis = self.getMazeDistance(pos, food)
      if dis < min_dis:
        min_dis = dis
        min_food = food
    next_foodlist.remove(min_food)
    return min_dis + self.greedyHeuristic(min_food, next_foodlist)

  def getMemberID(self, gameState):
    teamID = self.getTeam(gameState)
    teamID.remove(self.index)
    return teamID[0]

  def getHomeBorader(self, gameState):
    """
    Get the boarder line position in home territory.
    Parameters:
    -------------
    gameState:
      current game state
    Returns:
    -------------
    boarder_list: List()
      an array of tuples containing coordinate for each boarder position
    """
    # boarder line
    x = self.width // 2
    # red home boarder
    if self.red:
      x -= 1

    boarder_list = [(x, y) for y in range(1, self.height - 1) if not gameState.hasWall(x, y)]
    return boarder_list

  def getEnemyBorader(self, gameState):
    """
    Get the boarder line position in enemy territory.
    Parameters:
    -------------
    gameState:
      current game state
    Returns:
    -------------
    boarder_list: List()
      an array of tuples containing coordinate for each boarder position
    """
    # boarder line
    x = self.width // 2
    # red home boarder
    if not self.red:
      x -= 1

    boarder_list = [(x, y) for y in range(1, self.height - 1) if not gameState.hasWall(x, y)]
    return boarder_list

  def calculateFood(self, gameState, xrange, yrange, defend=False):
    """
    Calculate the number of food dots, given a territory(home or enemy) and
    a certain square range.
    Parameters:
    ---------------
    gameState:
      current game state
    xrange, yrange: range
      range of x axis and y axis
    defend: boolean
      specify whether we calculate home territory or enemy territory
    Returns:
    ---------------
    cnt: int
      the number of food dots
    """
    cnt = 0
    for x in xrange:
      for y in yrange:
        if defend:
          if self.getFoodYouAreDefending(gameState)[x][y]:
            cnt += 1
        else:
          if self.getFood(gameState)[x][y]:
            cnt += 1
    return cnt

  def getFoodDensity(self, gameState):
    """
    Compute the density of each food dot in enemy territory, in particular,
    the number of dots within its limited scope.
    Parameters:
    ---------------
    gameState:
      current game state
    Returns:
    ---------------
    density_dict: dict()
      return a dictionary which maps from food dot coordinate to the number of
      dots nearby
    """
    starttime = time.time()
    foodList = self.getFood(gameState).asList()
    density_dict = {}
    scope = 3  # 3 by 3 neighbouring scope

    for (x, y) in foodList:
      if time.time() - starttime > 0.2:
        break
      x_min, x_max = max(1, x - scope), min(self.width - 1, x + scope)
      y_min, y_max = max(1, y - scope), min(self.height - 1, y + scope)
      density_dict[(x, y)] = self.calculateFood(gameState, range(x_min, x_max + 1), range(y_min, y_max + 1))

    return density_dict

  def getFoodDensityYouAreDefending(self, gameState):
    """
    Compute the density of each food dot in home territory, in particular,
    the number of dots within its limited scope.
    Parameters:
    ---------------
    gameState:
      current game state
    Returns:
    ---------------
    density_dict: dict()
      return a dictionary which maps from food dot coordinate to the number of
      dots nearby
    """
    starttime = time.time()
    foodList = self.getFoodYouAreDefending(gameState).asList()
    density_dict = {}  # mapping from food pos to number of neighbours

    scope = 3  # 3 by 3 neighbouring scope
    for (x, y) in foodList:
      if time.time() - starttime > 0.2:
        break
      x_min, x_max = max(1, x - scope), min(self.width - 1, x + scope)
      y_min, y_max = max(1, y - scope), min(self.height - 1, y + scope)
      density_dict[(x, y)] = self.calculateFood(gameState, range(x_min, x_max + 1), range(y_min, y_max + 1), True)
    return density_dict

  def getHomeTerritory(self):
    """
    returns x axis and y axis range of home territory
    """
    y_range = range(1, self.height - 1)
    if self.red:
      x_range = range(1, self.width // 2)
      return (x_range, y_range)
    else:
      x_range = range(self.width // 2, self.width - 1)
      return (x_range, y_range)

  def getEnemyTerritory(self):
    """
    returns x axis and y axis range of enemy territory
    """
    y_range = range(1, self.height - 1)
    if self.red:
      x_range = range(self.width // 2, self.width - 1)
      return (x_range, y_range)
    else:
      x_range = range(1, self.width // 2)
      return (x_range, y_range)

  def getHomeBoarderWithoutCorner(self, gameState):

    self.specifyGlobalInfo(gameState)
    # boarder line
    x = self.width // 2
    # red home boarder
    if self.red:
      x -= 1

    boarder_list = [(x, y) for y in range(1, self.height - 1) if
                    not gameState.hasWall(x, y) and (x, y) not in self.deadEndSet['home']]
    return boarder_list

  def eatFoodAction(self, gameState):
    """
    Given the current state, output an action which leads to eating
    food action.
    Parameters:
    ---------------
    gameState:
      current game state
    Returns:
    ---------------
    best_action:
      a valid action whose goal is eating food dots
    """
    best_action = None
    min_distance = self.getMazeDistance(self.getClosestFood(gameState), self.position)
    best_pos = (); candidates = []
    for next_pos, action in getNeighbours(gameState, self.position).items():
      if (not self.canReverse) and (next_pos == self.lastPosition or next_pos in self.gateFoodMap['enemy']):
        continue
      candidates.append((next_pos, action))
    for pos, action in candidates:
      distance = self.getMazeDistance(pos, self.getClosestFood(gameState))  # next state distance
      if distance < min_distance:
        best_action = action
        best_pos = pos
        self.canReverse = True
        break
    else:
      if candidates:
        best_pos, best_action = random.choice(candidates)

    if best_pos in self.gateFoodMap['enemy'] and self.gateFoodMap['enemy'][best_pos]:
      self.recordInfo(self.position, best_pos)

    return best_action

  def getRewardMap(self, gameState, mode='attack'):
    """
    Given the current game state and which mode we are interested in,
    output a reward map in which each valid coordinate corresponds a
    real value of reward.
    Parameters:
    ---------------
    gameState:
      current game state
    mode: str
      can be 'attack' mode or 'defend' mode
    Returns:
    ---------------
    reward_dict: Dict
      a reward map, that assigns each coordinate with a real value
    """

    # determine which part we are interested in
    if mode == 'attack':
      attack_territory = self.enemyTerritory
      defend_territory = self.homeTerritory
      foodMap = self.getFood(gameState)
      capsuleMap = self.getCapsules(gameState)
    else:
      attack_territory = self.homeTerritory
      defend_territory = self.enemyTerritory
      foodMap = self.getFoodYouAreDefending(gameState)
      capsuleMap = self.getCapsulesYouAreDefending(gameState)

    reward_dict = {}  # a dictionary maps from coordinate to reward
    xrange, yrange = attack_territory

    for x in xrange:
      for y in yrange:
        if (x, y) in foodMap.asList():
          reward_dict[(x, y)] = foodScore  # assign food score to coordinates with food dot
        elif (x, y) in capsuleMap:
          reward_dict[(x, y)] = capsuleScore  # assign capsule score to coordinates with capsule
        else:
          if not gameState.hasWall(x, y):
            reward_dict[(x, y)] = blankEnemyScore  # assign blank enemy score in blank enemy territory

    xrange, yrange = defend_territory
    for x in xrange:
      for y in yrange:
        if not gameState.hasWall(x, y):
          reward_dict[(x, y)] = blankHomeScore  # assign blank home score in blank home territory

    return reward_dict

  def specifyGlobalInfo(self, gameState):
    self.rewardMap = {'attack': self.getRewardMap(gameState, 'attack'),
      'defend': self.getRewardMap(gameState, 'defend')}
    sp_home = SpecialPositions(gameState, self.red, 'defend', SmartAgent)
    sp_enemy = SpecialPositions(gameState, self.red, 'attack', SmartAgent)
    self.gateFoodMap = {'home': sp_home.getGateFoodDict(), 'enemy': sp_enemy.getGateFoodDict()}
    self.deadEndSet = {'home': sp_home.getDeadEndSet(), 'enemy': sp_enemy.getDeadEndSet()}
    self.corridorSet = {'home': sp_home.getCorridorSet(), 'enemy': sp_enemy.getCorridorSet()}
    self.foodCarrying = gameState.getAgentState(self.index).numCarrying
    self.foodCarryingMember = gameState.getAgentState(self.memberID).numCarrying
    self.foodLeft = len(self.getFood(gameState).asList())
    self.foodLeftYouAreDefending = len(self.getFoodYouAreDefending(gameState).asList())
    self.position = gameState.getAgentPosition(self.index)
    if self.position == self.start:
      self.eraseInfo()

  def isEscape(self, gameState):
    if self.getEnemyIdxPosition(gameState):
      idx_pos_dict = self.getEnemyIdxPosition(gameState)
      closest_idx = self.getClosestEnemyIndex(idx_pos_dict)
      idx, pos = closest_idx, idx_pos_dict[closest_idx]
      if self.getMazeDistance(self.position, pos) <= 5:
        if gameState.getAgentState(idx).scaredTimer > 5:
          return False
        return True
    return False

  def escapeAction(self, gameState):
    idx_pos_dict = self.getEnemyIdxPosition(gameState)
    dis = self.getEnemyDistance(self.position, idx_pos_dict)
    candidates = []; tie = []
    for next_pos, action in getNeighbours(gameState, self.position).items():
      if next_pos not in self.gateFoodMap['enemy'].keys():
        if self.getEnemyDistance(next_pos, idx_pos_dict) == dis:
          tie.append((next_pos, action))
        if self.getEnemyDistance(next_pos, idx_pos_dict) > dis:
          dis = self.getEnemyDistance(next_pos, idx_pos_dict)
          tie = []; tie.append((next_pos, action))
      else:
        if self.getClosestCapsule(gameState):
          if self.getMazeDistance(next_pos, self.getClosestCapsule(gameState)) < \
                  self.getMazeDistance(self.position, self.getClosestCapsule(gameState)):
            candidates.append((next_pos, action))
    candidates.extend(tie)

    # lead to capsule
    if candidates:
      if self.getClosestCapsule(gameState):
        for next_pos, action in candidates:
          if next_pos == self.getClosestCapsule(gameState):
            return action
          if self.getMazeDistance(next_pos, self.getClosestCapsule(gameState)) < \
                  self.getMazeDistance(self.position, self.getClosestCapsule(gameState)):
            return action
      # lead to food
      for next_pos, action in candidates:
        if self.getMazeDistance(next_pos, self.getClosestFood(gameState)) < \
                self.getMazeDistance(self.position, self.getClosestFood(gameState)):
          return action
      return random.choice(candidates)[1]

  def getClosestFood(self, gameState):
    closest_food = None
    closest_distance = float('inf')
    for food in self.getFood(gameState).asList():
      distance = self.getMazeDistance(self.position, food)
      if distance < closest_distance:
        closest_distance = distance
        closest_food = food
    return closest_food

  def getClosestCapsule(self, gameState):
    closest_capsule = None
    closest_distance = float('inf')
    if self.getCapsules(gameState):
      for capsule in self.getCapsules(gameState):
        distance = self.getMazeDistance(self.position, capsule)
        if distance < closest_distance:
          closest_distance = distance
          closest_capsule = capsule
      return closest_capsule
    return None

  def getEnemyIdxPosition(self, gameState):
    dicts = {}
    for enemy in self.getOpponents(gameState):
      enemy_state = gameState.getAgentState(enemy)
      if enemy_state.getPosition() and not enemy_state.isPacman:
        # dis = self.getMazeDistance(self.position, enemy_state.getPosition())
        position = enemy_state.getPosition()
        if self.getMazeDistance(self.position, position) <= 5:
          dicts[enemy] = position
    return dicts if dicts else None

  def getEnemyIdxPositionTurnBack(self, gameState):
    dicts = {}
    for enemy in self.getOpponents(gameState):
      enemy_state = gameState.getAgentState(enemy)
      if enemy_state.getPosition() and not enemy_state.isPacman:
        # dis = self.getMazeDistance(self.position, enemy_state.getPosition())
        position = enemy_state.getPosition()
        dicts[enemy] = position
    return dicts if dicts else None

  def getEnemyDistance(self, pos, enemy_dict):
    if enemy_dict:
      distance = 0
      for idx, enemy_pos in enemy_dict.items():
        distance += self.getMazeDistance(pos, enemy_pos)
      return distance

  def getClosestEnemyIndex(self, enemy_dict):
    if enemy_dict:
      closest_dis = float('inf')
      cloest_idx = None
      for idx, pos in enemy_dict.items():
        if self.getMazeDistance(self.position, pos) < closest_dis:
          cloest_idx = idx; closest_dis = self.getMazeDistance(self.position, pos)
      return cloest_idx

  def bfsHome(self, gameState, source, target):
    path = []
    queue = util.Queue()
    closed = [source]
    xrange, _ = self.homeTerritory
    queue.push((source, path))
    while not queue.isEmpty():
      cur_pos, path = queue.pop()
      if cur_pos == target:
        return path
      for next_pos, action in getNeighbours(gameState, cur_pos).items():
        if next_pos[0] in xrange and next_pos not in closed:
          closed.append(next_pos)
          queue.push((next_pos, path + [action]))

  def findAttackPoint(self, gameState):
    foodDensity = self.getFoodDensity(gameState)
    max_den_pos = max(foodDensity, key=foodDensity.get)
    attackPoint = ()
    min_dis = float('inf')
    for coord in self.homeBoarder:
      if abs(coord[1] - max_den_pos[1]) < min_dis:
        min_dis = abs(coord[1] - max_den_pos[1])
        attackPoint = coord
    return attackPoint

  def goAttackPointAction(self, gameState):

    if not self.attackPoint:
      self.attackPoint = self.findAttackPoint(gameState)
    return self.oneStepCloserAction(gameState, self.position, self.attackPoint)

  def isAttack(self, gameState, threshold):
    for enemy in self.getOpponents(gameState):
      enemy_state = gameState.getAgentState(enemy)
      if enemy_state.getPosition() and not enemy_state.isPacman and enemy_state.scaredTimer == 0:
        if self.getMazeDistance(self.position, enemy_state.getPosition()) <= threshold:
          return False
    return True

  def wanderAction(self, gameState):
    candidate_actions = gameState.getLegalActions(self.index)
    for action in candidate_actions.copy():
      successor = gameState.generateSuccessor(self.index, action)
      if successor.getAgentState(self.index).isPacman:
        candidate_actions.remove(action)

    return random.choice(candidate_actions)

  def recordInfo(self, cur_pos, next_pos):
    self.safePos = cur_pos
    self.gatePos = next_pos
    self.isInGate = True

  def eraseInfo(self):
    self.gatePos = None
    self.safePos = None
    self.isInGate = False

  def hasToTurnBack(self, gameState):
    # no food in a gate
    if not self.gateFoodMap['enemy'][self.gatePos]:
      return True

    if self.getEnemyIdxPositionTurnBack(gameState):
      idx_pos_dict = self.getEnemyIdxPositionTurnBack(gameState)
      closest_idx = self.getClosestEnemyIndex(idx_pos_dict)
      idx, pos = closest_idx, idx_pos_dict[closest_idx]
      if self.getMazeDistance(pos, self.safePos) - self.getMazeDistance(self.position, self.safePos) <= 3:
        if gameState.getAgentState(idx).scaredTimer > 5:
          return False
        return True
    return False

  def turnBackAction(self, gameState):
    action = self.oneStepCloserAction(gameState, self.position, self.safePos)
    if not action:
      return None
    next_pos = gameState.generateSuccessor(self.index, action).getAgentPosition(self.index)

    if next_pos == self.safePos:
      self.eraseInfo()

    return action

  def oneStepCloserAction(self, gameState, source, target):
    cur_dis = self.getMazeDistance(source, target)
    for next_pos, action in getNeighbours(gameState, source).items():
      if self.getMazeDistance(next_pos, target) < cur_dis:
        return action

  def chooseAttackPoints(self, gameState):
    attack_points = []
    for candidate in self.homeBoarder:
      if self.red:
        if not gameState.hasWall(candidate[0] + 1, candidate[1]):
          if not gameState.hasWall(candidate[0] + 2, candidate[1]):
            if not gameState.hasWall(candidate[0] + 3, candidate[1]):
              attack_points.append(candidate)
            else:
              if not gameState.hasWall(candidate[0] + 3, candidate[1] + 1) or \
                not gameState.hasWall(candidate[0] + 3, candidate[1] - 1):
                attack_points.append(candidate)
          else:
            if not gameState.hasWall(candidate[0] + 2, candidate[1] + 1) or \
                    not gameState.hasWall(candidate[0] + 2, candidate[1] - 1):
              attack_points.append(candidate)
      else:
        if not gameState.hasWall(candidate[0] - 1, candidate[1]):
          if not gameState.hasWall(candidate[0] - 2, candidate[1]):
            if not gameState.hasWall(candidate[0] - 3, candidate[1]):
              attack_points.append(candidate)
            else:
              if not gameState.hasWall(candidate[0] - 3, candidate[1] + 1) or \
                not gameState.hasWall(candidate[0] - 3, candidate[1] - 1):
                attack_points.append(candidate)
          else:
            if not gameState.hasWall(candidate[0] - 2, candidate[1] + 1) or \
                    not gameState.hasWall(candidate[0] - 2, candidate[1] - 1):
              attack_points.append(candidate)
    return attack_points

  def changeAttackPointAction(self, gameState):
    if not self.isChangedAttackPoint:
      ori_attack_point = self.attackPoint
      candidate_points = self.chooseAttackPoints(gameState)
      if ori_attack_point == self.position:
        candidate_points.remove(ori_attack_point)
      else:
        if ori_attack_point and (self.position in candidate_points):
          candidate_points.remove(ori_attack_point)
          candidate_points.remove(self.position)
      if not candidate_points:
        self.attackPoint = random.choice(self.homeBorder)
      else:
        self.attackPoint = random.choice(candidate_points)
      self.isChangedAttackPoint = True
    path = self.bfsHome(gameState, self.position, self.attackPoint)
    if not path:
      return random.choice(gameState.getLegalActions(self.index))

    if gameState.generateSuccessor(self.index, path[0]).getAgentPosition(self.index) == self.attackPoint:
      self.numWander = 0
      self.isChangedAttackPoint = False
    return path[0]

  def isRepeatingHome(self):
    if len(self.queue.list) < 5:
      return False
    pos_list = self.queue.list
    if (pos_list[0] in self.homeBoarder and pos_list[2] in self.homeBoarder
            and pos_list[1] in self.enemyBoarder and pos_list[3] in self.enemyBoarder):
      return True
    if pos_list[0] == pos_list[4] and pos_list[0][0] in self.homeTerritory[0]\
            and pos_list[4][0] in self.homeTerritory[0]:
      return True
    return False

  def isRepeatingEnemy(self):
    if len(self.queue.list) < 5:
      return False
    pos_list = self.queue.list
    if pos_list[0][0] in self.enemyTerritory[0] and pos_list[1][0] in self.enemyTerritory[0] and \
      pos_list[2][0] in self.enemyTerritory[0] and pos_list[3][0] in self.enemyTerritory[0] and\
      pos_list[4][0] in self.enemyTerritory[0] and pos_list[5][0] in self.enemyTerritory[0] and \
      (pos_list[0] == pos_list[2] == pos_list[4] and pos_list[1] == pos_list[3] == pos_list[5]):
      return True
    return False

  def repeatAction(self, gameState):
    for next_pos, action in getNeighbours(gameState, self.position).items():
      if self.red:
        if next_pos[0] < self.position[0]:
          return action
      else:
        if next_pos[0] > self.position[0]:
          return action
    legal_actions = gameState.getLegalActions(self.index)
    if self.lastAction in legal_actions:
      legal_actions.remove(self.lastAction)
    return random.choice(legal_actions)

  def getPowerPacmanIndex(self, gameState):
    closest_idx = None; closest_dis = float('inf')
    for enemy in self.getOpponents(gameState):
      enemy_state = gameState.getAgentState(enemy)
      if enemy_state.getPosition() and enemy_state.isPacman:
        if self.getMazeDistance(self.position, enemy_state.getPosition()) < closest_dis:
          closest_dis = self.getMazeDistance(self.position, enemy_state.getPosition())
          closest_idx = enemy
    return closest_idx

  def isPowerPacman(self, gameState):
    my_state = gameState.getAgentState(self.index)
    enemy_idx = self.getPowerPacmanIndex(gameState)
    if enemy_idx:
      pos = gameState.getAgentState(enemy_idx).getPosition()
      if self.getMazeDistance(self.position, pos) <= 3:
        if my_state.scaredTimer > 0:
          return True
    return False

  def escapePacmanAction(self, gameState):
    enemy_idx = self.getPowerPacmanIndex(gameState)
    if enemy_idx:
      pos = gameState.getAgentState(enemy_idx).getPosition()
      for next_pos, action in getNeighbours(gameState, self.position).items():
        if next_pos not in self.gateFoodMap['home']:
          if self.getMazeDistance(next_pos, pos) > self.getMazeDistance(self.position, pos):
            return action

  ########################
  # Go - Home - Strategy #
  #         START        #
  ########################

  def getGoHomePath(self, gameState):
    """
    Given the current state, output a path which leads to home.
    (A* verison)
    Returns:
    ---------------
    a valid list of actions whose goal is go back home
    """
    heuristicPath = self.aStarSearch(self.goHomeHeuristic, gameState)
    pos = gameState.getAgentPosition(self.index)
    enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
    ghosts = [enemy for enemy in enemies if not enemy.isPacman and enemy.getPosition() is not None]

    if len(ghosts) != 0:
      ghost_distance = min([self.getMazeDistance(pos, ghost.getPosition()) for ghost in ghosts])
      if ghost_distance < 6:
        return heuristicPath[:1]
    return heuristicPath[:2]

  def getAstarAction(self, gameState):
    # execute action from A star search
    if not self.goHomePath:
      self.goHomePath = self.getGoHomePath(gameState)

    # this should always be true but need to be safe
    if self.goHomePath:
      aStarAction = self.goHomePath.pop(0)
    else:
      aStarAction = random.choice(gameState.getLegalActions(self.index))
    return aStarAction

  def hasVisibleEnemy(self, gameState):
    enemies = [gameState.getAgentState(i) for i in
               self.getOpponents(gameState)]  # enemy should be sorted by order of index
    ghosts = [enemy for enemy in enemies if not enemy.isPacman and enemy.getPosition() is not None]

    return ghosts

  def getGhostDistance(self, gameState, ghosts):
    pos = gameState.getAgentState(self.index).getPosition()
    ghost_distance_list = []
    # current distance to home and ghosts
    for ghost in ghosts:
      ghost_distance = self.getMazeDistance(pos, ghost.getPosition())
      ghost_distance_list.append(ghost_distance)
    return ghost_distance_list

  def getHomeDistance(self, gameState):
    """
    get minimum distance to all available home border point, return int
    """
    myPos = gameState.getAgentState(self.index).getPosition()
    # Compute distance to the nearest board point
    minBoard = min([self.getMazeDistance(myPos, board) for board in self.homeBoarder])
    return minBoard

  def getExtraFoodAction(self, gameState):
    foodLeft = len(self.getFood(gameState).asList())
    actions = gameState.getLegalActions(self.index)
    for nextStep in actions:
      successor = gameState.generateSuccessor(self.index, nextStep)
      foodLeft_next = len(self.getFood(successor).asList())
      if foodLeft_next < foodLeft:
        return nextStep

  def getFoodDistance(self, gameState):
    """
    get minimum distance to all available home border point, return int
    """
    myPos = gameState.getAgentState(self.index).getPosition()
    # Compute distance to the nearest board point

    closestCapsule = self.getClosestCapsule(gameState)
    try:
      minGoal = self.getMazeDistance(myPos, closestCapsule)
    except:
      minGoal = self.getHomeDistance(gameState)
    return minGoal

  def isScare(self, gameState):
    """
    return if enemy around will remain scared in the next 5 steps
    """
    # opponents = self.getOpponents(gameState)
    # ghosts = []
    # # ghosts = self.hasVisibleEnemy(gameState)
    # isScared = False
    # for opponentIdx in opponents:
    #   opponent = gameState.getAgentState(opponentIdx)
    #   if not opponent.isPacman:
    #     ghosts.append(opponent)
    #
    isScared = False
    enemies = [gameState.getAgentState(i) for i in self.getOpponents(gameState)]
    ghosts = [enemy for enemy in enemies if not enemy.isPacman] # and enemy.getPosition() is not None

    if ghosts:
      if len(ghosts) == 1 and ghosts[0].scaredTimer > 5:  # 40 steps countdown
        isScared = True
      elif len(ghosts) == 2: # 2 enemies are both at ghost state
        ghostAround = [enemy for enemy in ghosts if enemy.getPosition() is not None]
        if ghostAround:
          try: #try to get the closest ghost and its scared time
            distances = self.getGhostDistance(gameState, ghostAround)
            minDist = float('inf')
            closestIdx = None
            for idx, distance in enumerate(distances):
              if minDist >= distance:
                minDist = distance
                closestIdx = idx
            if ghosts[closestIdx].scaredTimer > 5:  # 40 steps countdown
              isScared = True
          except:
            pass
        else: # if no ghost around, get the min time of the two
          ghost1 = ghosts[0].scaredTimer
          ghost2 = ghosts[1].scaredTimer
          if min(ghost1, ghost2) > 5:
            isScared = True

    return isScared

  def getDogingAction(self, gameState, aStarAction, ghosts, rev, goHome = True):
    # check if enemy is scared
    if self.isScare(gameState):
      return None

    # even if ghost is at least 5 steps away, we still should not execute plan if it is walking towards ghost
    actions = gameState.getLegalActions(self.index)
    validActions = []
    nextDistances = util.Counter()

    # # get all corner and gate position
    dangerPos = self.deadEndSet['enemy']
    dangerPos |= self.corridorSet['enemy']

    for action in actions:
      isValidAction = True
      successor = self.getSuccessor(gameState, action)
      ghostDistanceListSuccessor = self.getGhostDistance(successor, ghosts)
      ghostDistanceList = self.getGhostDistance(gameState, ghosts)

      if ghostDistanceList:  # this would be true when ghost is invisible but agent is on its way of dodging
        for index in range(len(ghostDistanceList)):
          if ghostDistanceList[index] >= ghostDistanceListSuccessor[index]:  # action gets closer to ghost
            isValidAction = False
      if action == Directions.STOP:
        isValidAction = False
      if action == rev and self.isDodging:  # ensure no turning back when dodging
        isValidAction = False
      successorPos = successor.getAgentState(self.index).getPosition()

      if successorPos in dangerPos:
        isValidAction = False
      if isValidAction:
        validActions.append(action)
      # print("in dodging, validAction:", validActions)

      if goHome:
        nextDistances[action] = self.getHomeDistance(successor)
      else:
        nextDistances[action] = self.getFoodDistance(successor)
      # print("in dodging, nextDistances: ", nextDistances)

    if validActions:
      bestAction = self.bestNext(validActions, nextDistances)
      return bestAction
      # return random.choice(validActions)

  def bestNext(self, validActions, nextHomeDistances):
    minHomeDistance = float('inf')
    bestAction = None
    for action in validActions:
      if minHomeDistance > nextHomeDistances[action]:
        minHomeDistance = nextHomeDistances[action]
        bestAction = action
    return bestAction

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a grid position (location tuple).
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):
      # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def aStarSearch(self, heuristic, gameState):
    """
    A-star search algorithm.
    Parameters:
    ---------------
    gameState:
      current game state
    heuristic:
      problem heuristic function
    Returns:
    ---------------
    a list of valid actions whose toward goal states
    """
    startTime = time.time()
    # this is the position, naming may be confusing since it's from assignment 1, change later
    startState = (gameState.getAgentPosition(self.index))

    startNode = (startState, [], 0)  # position + sequence of actions + g(s)
    fringe = util.PriorityQueue()
    fringe.push(startNode, 0)
    visited = set()
    bestG = {}  # check is there a less cost to get each state

    while fringe.isEmpty() == False:
      node = fringe.pop()
      currentState, actions, cost = node[0], node[1], node[2]

      if currentState not in visited or cost < bestG[currentState]:
        visited.add(currentState)
        bestG[currentState] = cost

        if self.isGoalState(currentState) or time.time() - startTime > 0.5:
          if time.time() - startTime > 0.5:
            pass
            # print(time.time() - startTime, "second used, return incomplete search")
          return actions

        for successor in self.getSearchSuccessors(gameState, currentState):
          info = {}
          newHeuristicValue = cost + 1 + heuristic(successor[0], gameState, info)
          newNode = (successor[0], actions + [successor[1]], cost + 1)
          fringe.update(newNode, newHeuristicValue)

  def goHomeHeuristic(self, state, gameState, info):
    pos = state
    # min_dis = float('inf')
    # for border in self.homeBoarder:
    #   dis = self.getMazeDistance(pos, border)
    #   if dis < min_dis:
    #     min_dis = dis
    # heuristic = min_dis

    heuristic = self.greedyHeuristic(pos, self.homeBoarder)
    return heuristic

  def isGoalState(self, state):
    """
    goal checking for the a star search.
    """
    return state in self.homeBoarder

  def getSearchSuccessors(self, gameState, state):
    successors = []
    walls = gameState.getWalls()
    for direction in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
      x, y = state
      dx, dy = Actions.directionToVector(direction)
      nextx, nexty = int(x + dx), int(y + dy)
      if not walls[nextx][nexty]:
        successors.append(((nextx, nexty), direction))
    return successors

  def escapeAndGoHomeAction(self, gameState):
    idx_pos_dict = self.getEnemyIdxPosition(gameState)
    dis = self.getEnemyDistance(self.position, idx_pos_dict)
    candidates = []; tie = []
    for next_pos, action in getNeighbours(gameState, self.position).items():
      if next_pos not in self.gateFoodMap['enemy'].keys():
        if self.getEnemyDistance(next_pos, idx_pos_dict) == dis:
          tie.append((next_pos, action))
        if self.getEnemyDistance(next_pos, idx_pos_dict) > dis:
          dis = self.getEnemyDistance(next_pos, idx_pos_dict)
          tie = []; tie.append((next_pos, action))
      else:
        if self.getClosestCapsule(gameState):
          if self.getMazeDistance(next_pos, self.getClosestCapsule(gameState)) < \
                  self.getMazeDistance(self.position, self.getClosestCapsule(gameState)):
            candidates.append((next_pos, action))
    candidates.extend(tie)

    # lead to home point
    for next_pos, action in candidates:
      if self.getMazeDistance(next_pos, self.getClosestHomePoint(gameState)) < \
              self.getMazeDistance(self.position, self.getClosestHomePoint(gameState)):
        return action

    # lead to capsule
    if candidates:
      if self.getClosestCapsule(gameState):
        for next_pos, action in candidates:
          if next_pos == self.getClosestCapsule(gameState):
            return action
          if self.getMazeDistance(next_pos, self.getClosestCapsule(gameState)) < \
                  self.getMazeDistance(self.position, self.getClosestCapsule(gameState)):
            return action

      return random.choice(candidates)[1]

  def bfsEnemy(self, gameState, source, target):
    path = []
    queue = util.Queue()
    closed = [source]
    xrange, _ = self.enemyTerritory
    queue.push((source, path))
    while not queue.isEmpty():
      cur_pos, path = queue.pop()
      if cur_pos == target:
        return path
      for next_pos, action in getNeighbours(gameState, cur_pos).items():
        if next_pos[0] in xrange and next_pos not in closed:
          closed.append(next_pos)
          queue.push((next_pos, path + [action]))

  def goHomePointAction(self, gameState):
    best_action = None
    min_distance = self.getMazeDistance(self.getClosestHomePoint(gameState), self.position)
    best_pos = (); candidates = []
    for next_pos, action in getNeighbours(gameState, self.position).items():
      if (not self.canReverse) and (next_pos == self.lastPosition or next_pos in self.gateFoodMap['enemy']):
        continue
      candidates.append((next_pos, action))
    for pos, action in candidates:
      distance = self.getMazeDistance(pos, self.getClosestHomePoint(gameState))  # next state distance
      if distance < min_distance:
        best_action = action
        best_pos = pos
        self.canReverse = True
        break
    else:
      if candidates:
        best_pos, best_action = random.choice(candidates)

    return best_action

  def getGoHomeAction(self, gameState):
    if self.position in self.getGoHomePoints(gameState):
      if self.red:
        return 'West'
      else:
        return 'East'

    if self.isInGate:
      action = self.turnBackAction(gameState)
    else:
      self.eraseInfo()
      if self.isEscape(gameState):
        action = self.escapeAndGoHomeAction(gameState)
        self.canReverse = False
      else:
        action = self.goHomePointAction(gameState)
    if self.isRepeatingEnemy():
      action = self.repeatAction(gameState)

    if len(self.queue.list) >= 6:
      self.queue.pop()
      self.queue.push(self.position)
    else:
      self.queue.push(self.position)

    self.lastPosition = self.position
    self.lastAction = action

    return action

  def getClosestHomePoint(self, gameState):
    goHomePoints = self.getGoHomePoints(gameState)
    closest_point = None
    closest_distance = float('inf')
    for home_point in goHomePoints:
      distance = self.getMazeDistance(self.position, home_point)
      if distance < closest_distance:
        closest_distance = distance
        closest_point = home_point
    return closest_point

  def getGoHomePoints(self, gameState):
    goHomePoints = []
    for x, y in self.enemyBoarder:
      if self.red:
        if not gameState.hasWall(x-1, y):
          goHomePoints.append((x, y))
      else:
        if not gameState.hasWall(x+1, y):
          goHomePoints.append((x, y))
    return goHomePoints


  """
  1. identify enemies character before making a decision # already implemented in dodging action
  2. be mindful of time left in the game
  3. check agent's distance to home
  4. dynamic threshold for carrying based on grid size and food count 
  """
  def chooseStrategy(self, gameState):
    eatFood = True

    foodCarrying = gameState.getAgentState(self.index).numCarrying
    foodLeft = len(self.getFood(gameState).asList())

    # mapsize and foodCount: dynamic threshold for carry limit based on foodDensity and the size of map
    width = gameState.data.layout.width
    height = gameState.data.layout.height
    mapSize = (width * height)
    threshold = 3
    foodDensity = foodLeft / mapSize # default one is 0.04 max
    # crowedCapture: 0.126

    # check agent's distance to home
    distance2boarder = self.getHomeDistance(gameState)
    timeLeft = int(gameState.data.timeleft / 4)

    if mapSize > 150:
      threshold = int(2 * foodDensity * foodLeft)
      if threshold < 5:
        threshold = 5
    else: # for small maps, agent is more conservetive
      threshold = int(foodDensity * foodLeft)
      if threshold < 4:
        threshold = 4

    # Go home if very close to ghost
    ghosts = self.hasVisibleEnemy(gameState)

    # strategy decisions
    # agent carrying food, (go home only when carrying)
    if foodCarrying:
      # if there is no time left for agent or agent is close to border, go home
      if timeLeft - 10 <= distance2boarder or distance2boarder <= 2:
        # if self.red:
        #   print('1')
        eatFood = False

      # far away from border and have enough time
      else:

        # if agent eat all the food, go home
        if foodLeft <= 2:
          # if self.red:
          #   print('2')
          eatFood = False

        # agent carry food but not done
        else:
          # if ghost around and no more capsule left, if ghost not scared go home
          if ghosts and min(self.getGhostDistance(gameState, ghosts)) < 5 and not self.getCapsules(gameState):
            if not self.isScare(gameState) and ghosts and min(self.getGhostDistance(gameState, ghosts)) < 5:
              # if self.red:
              #   print('3')
              eatFood = False

          # if carrying larger than threhold,
          if foodCarrying >= threshold:
            if not self.isScare(gameState): # if ghost not scared(does not eat capsule), time to go home
              # if self.red:
              #   print('4')
              eatFood = False
            elif foodCarrying >= 2*threshold: # if ghost scared but carrying 1.5 threshold, also need to go home
              # if self.red:
              #   print('5')
              eatFood = False

          # if no defensive opponents, continue to eat food, (intended to overwrite the above 2 actions)
          enemy = self.opponents
          if gameState.getAgentState(enemy[0]).isPacman and gameState.getAgentState(enemy[1]).isPacman:
            # if self.red:
            #   print('6')
            eatFood = True

    # if self.red:
    #   print("mapSize:", mapSize, "food density:", foodDensity, "threshold:", threshold,  "timeLeft:", timeLeft,
    #       "distance2boarder:", distance2boarder, "food carrying:", foodCarrying, "foodLeft:", foodLeft, "is eatFood:", eatFood)
    return eatFood

  def eatFoodStrategy(self, gameState):
    if not gameState.getAgentState(self.index).isPacman:
      self.canReverse = True
      if self.numWander >= 2:
        action = self.changeAttackPointAction(gameState)
      else:
        if not self.isAttack(gameState, 3):
          action = self.wanderAction(gameState)
          if self.red:
            print('wander')
          self.numWander += 1
        else:
          if self.isPowerPacman(gameState):
            action = self.escapePacmanAction(gameState)
            if self.red:
              print('escape pacman')
          else:
            action = self.eatFoodAction(gameState)
          if self.red:
            print('eat food')
    else:
      self.numWander = 0
      if self.isInGate:
        if self.hasToTurnBack(gameState):
          action = self.turnBackAction(gameState)
          if self.red:
            print('turn back')
        else:
          action = self.eatFoodAction(gameState)
          if self.red:
            print('eat food')
      else:
        if self.isEscape(gameState):
          self.canReverse = False
          action = self.escapeAction(gameState)
          if self.red:
            print('escape')
        else:
          action = self.eatFoodAction(gameState)
          if self.red:
            print('eat food')
    if self.isRepeatingHome():
      if self.red:
        print('isRepeatingHome')
      self.numWander = 2
    if self.isRepeatingEnemy():
      if gameState.getAgentState(self.index).numCarrying == 0:
        self.numWander = 2
      if self.red:
        print('isRepeatingEnemy')
      action = self.repeatAction(gameState)

    if len(self.queue.list) >= 6:
      self.queue.pop()
      self.queue.push(self.position)
    else:
      self.queue.push(self.position)

    self.lastPosition = self.position
    self.lastAction = action
    return action

  def chooseAction(self, gameState):

    '''
    You should change this in your own agent.
    '''
    self.specifyGlobalInfo(gameState)  # get global information
    action = None

    eatFood = self.chooseStrategy(gameState)

    if eatFood:
      # strategy checking above, the below is eat food action impletementation
      action = self.eatFoodStrategy(gameState)

    else:
      action = self.getGoHomeAction(gameState)
      if self.red:
        print('home')
    if not action:
      action = random.choice(gameState.getLegalActions(self.index))
    return action

  ########################
  # Go - Home - Strategy #
  #         END          #
  ########################
######################################
#####  defensive
######################################
class defensiveAgent(SmartAgent):

  def chooseAction(self, gameState):
    '''
    Choosing the next action for the defense agent.
    '''
    start = time.time()
    actions = gameState.getLegalActions(self.index)
    enemies = [gameState.getAgentState(i) for i in self.opponents]
    observeInvaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    if gameState.getAgentState(self.index).scaredTimer == 0 or len(observeInvaders) == 0:
      bestaction = self.useBFSChoseAction(gameState)
    else:
      self.defensePath = []
      bestaction = self.useFeatureWeightChoseAction(gameState)[0]
    if bestaction:
      # print('chose action time for defendent agent %d: %.4f' % (self.index, time.time() - start))
      return bestaction
    else:
      self.defensePath = []
      # print('chose action time for defendent agent %d: %.4f' % (self.index, time.time() - start))
      return random.choice(actions)

  def useBFSChoseAction(self, gameState):
    '''
    Method of using BFS search to find best action
    '''
    start = time.time()
    self.specifyGlobalInfo(gameState)

    actions = gameState.getLegalActions(self.index)
    mystate = gameState.getAgentState(self.index)

    # If I am not defensing (I'm a Pacman currently), execute going home action
    if mystate.isPacman:
      self.defensePath = []
      return self.getGoHomeAction(gameState)

    enemies = [gameState.getAgentState(i) for i in self.opponents]
    invaders = [a for a in enemies if a.isPacman]
    observeInvaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    foodsPos = set(self.getFoodYouAreDefending(gameState).asList())

    pregameState = self.getPreviousObservation()
    preinvaders = []
    prefoodsPos = foodsPos
    if pregameState:
      preenemies = [pregameState.getAgentState(i) for i in self.opponents]
      preinvaders = [a for a in preenemies if a.isPacman]
      prefoodsPos = set(self.getFoodYouAreDefending(pregameState).asList())
    # finding the food which is latest eaten
    foodsPosDiff = prefoodsPos - foodsPos

    ## some conditions need to clean the defense path
    # 1 I am eaten, back to start position
    myPos = mystate.getPosition()
    if self.start == myPos:
      self.defensePath = []

    # 2 the num of invaders change
    if len(invaders) - len(preinvaders) == 1 or len(preinvaders) - len(invaders) == 1:
      self.defensePath = []

    # 3 the num of foodsPosDiff change
    if len(foodsPosDiff) > 0:
      self.defensePath = []

    if len(observeInvaders) >= 1:
      self.defensePath = []
      bestaction = self.chooseDefenseAction(gameState)

    else:  # len(observeInvadersPos) == 0
      bestaction = self.chooseDefenseAction(gameState)

    while True:
      # check whether time is enough, if it's more than 0.7s, return action directly
      if time.time() - start > 0.7:
        if bestaction:
          # print('findpath time for agent %d: %.4f' % (self.index, time.time() - start))
          return bestaction
        else:
          return random.choice(actions)

      # guarantee I am defending(not becoming pacman)
      successor = self.getSuccessor(gameState, bestaction)
      if not successor.getAgentState(self.index).isPacman:
        # print('findpath time for agent %d: %.4f' % (self.index, time.time() - start))
        return bestaction
      else:
        self.defensePath = []
        bestaction = random.choice(actions)
        continue

  def useFeatureWeightChoseAction(self, gameState):
    '''
     Method of using features and weights to find best action
    '''
    # self.defensePath = []
    # start = time.time()
    actions = gameState.getLegalActions(self.index)
    values = [self.evaluate(gameState, a) for a in actions]
    # print('eval time for agent %d: %.4f' % (self.index, time.time() - start))
    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]
    return [random.choice(bestActions)]

  def chooseDefenseAction(self, gameState):
    '''
    Choose the next action to execute
    '''
    actions = gameState.getLegalActions(self.index)
    if not self.defensePath:  # current defensePath is None
      goalPos = self.getDefenseGoalPos(gameState)
      self.defensePath = self.getDefensePath(gameState, goalPos)
      # print(goalPos)
      # print(self.defensePath)
    if self.defensePath:  # current defensePath is not None
      bestaction = self.defensePath.pop(0)
    else:
      bestaction = random.choice(actions)
    return bestaction

  def getDefenseGoalPos(self, gameState):
    '''
    Get best goal position for current gameState.
    When invader is observable, return it's position.
    When there is invader but it is not observable:
      case1: last observation(pregameState) I saw ghost(s), return nearest ghost pos
      case2: food(s) are eaten, return nearest eaten food pos
      case3: didn't see ghost and no foods are eaten, choose a dense food point
    when there is no invader, return a random border/attack point.
    '''
    mypos = gameState.getAgentState(self.index).getPosition()
    enemies = [gameState.getAgentState(i) for i in self.opponents]
    invaders = [a for a in enemies if a.isPacman]
    observeInvaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    observeInvadersPos = []
    if observeInvaders:
      observeInvadersPos = [a.getPosition() for a in observeInvaders]

    if len(observeInvadersPos) >= 1:
      return observeInvadersPos[0]
    else:  # len(observeInvadersPos) == 0
      if len(invaders) > 0:

        foodsPos = set(self.getFoodYouAreDefending(gameState).asList())
        pregameState = self.getPreviousObservation()
        observePreinvaders = []
        prefoodsPos = foodsPos
        if pregameState:
          preenemies = [pregameState.getAgentState(i) for i in self.opponents]
          observePreinvaders = [a for a in preenemies if a.isPacman and a.getPosition() != None]
          prefoodsPos = set(self.getFoodYouAreDefending(pregameState).asList())

        # finding the food which is eaten recently
        foodsPosDiff = prefoodsPos - foodsPos

        # case1: last observation(pregameState) I saw ghost(s), return nearest ghost pos
        if observePreinvaders:
          ghostPos = ()
          mindistoghost = 999
          for a in observePreinvaders:
            dis = self.getMazeDistance(mypos, a.getPosition())
            if dis < mindistoghost:
              mindistoghost = dis
              ghostPos = a.getPosition()
          return ghostPos

        # case2: food(s) are eaten, return nearest eaten food pos
        elif foodsPosDiff:
          mindistofood = 999
          foodPos = ()
          for food in foodsPosDiff:
            dis = self.getMazeDistance(mypos, food)
            if dis < mindistofood:
              mindistofood = dis
              foodPos = food
          return foodPos

        # case3: didn't see ghost and no foods are eaten, choose a dense food point
        else:
          return random.choice(self.homeBorderWithoutCorner)
        # else:
        #   self.specifyGlobalInfo(gameState)
        #   foodDensity = self.getFoodDensityYouAreDefending(gameState)
        #   if foodDensity:
        #     maxnum = max(foodDensity.values())
        #     bestFoodPos = []
        #     for pos, num in foodDensity.items():
        #       if num == maxnum and pos not in self.deadEndSet['home']:
        #         bestFoodPos.append(pos)
        #     if maxnum >= 3 and bestFoodPos:
        #       return random.choice(bestFoodPos)
        #     else:
        #       return random.choice(self.homeBorderWithoutCorner)
        #   else:
        #     return random.choice(self.homeBorderWithoutCorner)

      else:  # len(invaders) == 0
        return random.choice(self.homeBorderWithoutCorner)

  def getDefensePath(self, gameState, goalPos):
    '''
    Getting a whole path from current position to goal position.
    whenever using this function, set the initial variable self.defensePath is None.
    When BFS search time is within threshold or no invaders at the moment, using BFS search
    When BFS search time exceeds threshold and there is an invader, if the invader is observable
    using Feature Weights method to choose action, if the invader is not observable using the maze
    search method to choose action.
    '''

    self.defensePath = []
    enemies = [gameState.getAgentState(i) for i in self.opponents]
    invaders = [a for a in enemies if a.isPacman]
    observeInvaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
    if self.time == 0:
    # if self.time == 0 or len(invaders) == 0:
      return self.BFSSearch(gameState, goalPos)
    else:
      if len(observeInvaders) > 0:
        return self.useFeatureWeightChoseAction(gameState)
      else:
        # print('mazeaction')
        return self.MazeSearch(gameState)

  def MazeSearch(self, gameState):
    '''
    Using maze distance to find best action to goal Position
    '''
    starttime = time.time()
    actions = gameState.getLegalActions(self.index)
    actions.remove('Stop')
    mypos = gameState.getAgentState(self.index).getPosition()

    # if there are foods eaten, the goal position is the nearest food pos
    foodsPos = set(self.getFoodYouAreDefending(gameState).asList())
    pregameState = self.getPreviousObservation()
    prefoodsPos = foodsPos
    if pregameState:
      prefoodsPos = set(self.getFoodYouAreDefending(pregameState).asList())
    foodsPosDiff = prefoodsPos - foodsPos
    if foodsPosDiff:
      mindistofood = 999
      foodPos = ()
      for food in foodsPosDiff:
        dis = self.getMazeDistance(mypos, food)
        if dis < mindistofood:
          mindistofood = dis
          foodPos = food
      self.MazegoalPos = foodPos

    if self.getMazeDistance(self.MazegoalPos, mypos) <= 1:
      self.time = 0
      self.MazegoalPos = random.choice(self.homeBorderWithoutCorner)

    # print(f'mazegoalpos {self.MazegoalPos}')
    dis = self.getMazeDistance(mypos, self.MazegoalPos)
    for action in actions:
      successor = self.getSuccessor(gameState, action)
      newpos = successor.getAgentState(self.index).getPosition()
      newdis = self.getMazeDistance(newpos, self.MazegoalPos)
      if newdis < dis:
        # print('mazetime %d: %.4f' % (self.index, time.time() - starttime))
        return [action]
    else:
      # print('mazetime %d: %.4f' % (self.index, time.time() - starttime))
      return [random.choice(actions)]

  def BFSSearch(self, gameState, goalPos):
    '''
    BFS search, using to find optimal path
    '''
    start = time.time()
    from util import Queue
    queue = Queue()
    visited = set()
    actions = []
    queue.push((gameState, []))
    while not queue.isEmpty():
      currState, actions = queue.pop()
      legalactions = currState.getLegalActions(self.index)
      if time.time() - start > 0.6:
        self.time = 0.6
        if actions:
          return actions[0:3]
        else:
          return [random.choice(legalactions)]
      if currState.getAgentState(self.index).getPosition() == goalPos:
        self.time = 0
        return actions
      visited.add(currState)

      # generating successors (within my home territory)
      successors = []
      for action in legalactions:
        successor = self.getSuccessor(currState, action)
        # check whether my next possition is within my territory
        mypos = successor.getAgentState(self.index).getPosition()
        if self.red:
          if mypos[0] <= self.homeBorder[1]:
            successors.append((successor, [action]))
        elif not self.red:
          if mypos[0] >= self.homeBorder[0]:
            successors.append((successor, [action]))

      # expand nodes
      if successors:
        for successor, act in successors:
          if successor not in visited:
            queue.push((successor, actions + act))
    self.time = 0
    return actions

  def evaluate(self, gameState, action):
    """
    Computes a linear combination of features and feature weights
    """
    features = self.getFeatures(gameState, action)
    weights = self.getWeights(gameState, action)
    return features * weights

  def getFeatures(self, gameState, action):
    '''
    Getting features for evaluate defense action
    '''

    features = util.Counter()
    successor = self.getSuccessor(gameState, action)

    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()

    ## feature1: Computes whether we're on defense (1) or offense (0)
    features['onDefense'] = 1
    if myState.isPacman: features['onDefense'] = 0

    # get enemies agentState
    enemies = [successor.getAgentState(i) for i in self.opponents]
    # the invaders(pacman) we can observe
    invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]

    ## feature2: eat invader, fewer better
    features['numInvaders'] = len(invaders)

    ## feature3: chase the closest invader, less better
    currgameState = self.getCurrentObservation()
    currenemies = [currgameState.getAgentState(i) for i in self.opponents]
    currinvaders = [a for a in currenemies if a.isPacman and a.getPosition() != None]

    pregameState = self.getPreviousObservation()
    preinvaders = []
    if pregameState:
      preenemies = [pregameState.getAgentState(i) for i in self.opponents]
      preinvaders = [a for a in preenemies if a.isPacman and a.getPosition() != None]
      # dists = [self.getMazeDistance(myPos, a.getPosition()) for a in preinvaders]
      # print(dists)

    if len(invaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
      features['invaderDistance'] = min(dists)
    elif len(currinvaders) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in currinvaders]
      features['invaderDistance'] = min(dists)
    elif pregameState:
      if len(preinvaders) > 0:
        dists = [self.getMazeDistance(myPos, a.getPosition()) for a in preinvaders]
        features['invaderDistance'] = min(dists)
    else:
      features['invaderDistance'] = 15  # when the invaders are unobservable

    ## feature4: protect capsule, less better
    if self.defendingCapsule:
      disCapsule = [self.getMazeDistance(myPos, cap) for cap in self.defendingCapsule]
      features['capsuleDistance'] = min(disCapsule)

    ## feature5: protect food, more better
    x1, x2, y1, y2 = getHomeBorder(successor, self.red)
    x, y = int(myPos[0]), int(myPos[1])
    xrange = range(max(x1, x - 3), min(x2, x + 3) + 1)
    yrange = range(max(y1, y - 3), min(y2, y + 3) + 1)
    foodcnt = self.rangeFoodCount(successor, xrange, yrange)
    features['nearFoodCnt'] = foodcnt

    ## feature6: protect gate with most food, less better
    bestgates = []
    gatefoodDisc = self.gateFoodMap['home']
    # print(gatefoodDisc)
    maxnum = max(len(foods) for foods in gatefoodDisc.values())
    for gate in gatefoodDisc.keys():
      if gatefoodDisc[gate] == maxnum:
        bestgates.append(gate)
    disGate = [self.getMazeDistance(myPos, gate) for gate in bestgates]
    if disGate:
      features['bestGateDistance'] = min(disGate)

    ## feature7: avoid Stop action
    if action == Directions.STOP: features['stop'] = 1

    ## feature8: avoid reverse action
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1

    ## feature9: avoid staying in corner
    if myPos in self.deadEndSet['home']:
      features['stayCorner'] = 1

    ## feature10: protect food(get away of no food long way), less better
    foodlist = self.getFoodYouAreDefending(successor).asList()
    fooddis = [self.getMazeDistance(myPos, food) for food in foodlist]
    if fooddis:
      features['foodDistance'] = min(fooddis)

    ## feature11:
    if myState.scaredTimer > 0:
      if len(invaders) > 0:
        dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
        dist = min(dists)
        if dist <= 2:
          features['ScaredGhostToCloseToPacman'] = 1
    return features

  def getWeights(self, gameState, action):
    '''
    Getting weights for evaluate defense action
    '''
    return {'onDefense': 100, 'numInvaders': -1000, 'invaderDistance': -200, \
            'capsuleDistance': -3, 'nearFoodCnt': 2, 'bestGateDistance': -3, \
            'stop': -100, 'reverse': -2, 'stayCorner': -5, 'foodDistance': -2, \
            'ScaredGhostToCloseToPacman': -10000}

  def getSuccessor(self, gameState, action):
    """
    Finds the next successor which is a gameState at a grid position.
    """
    successor = gameState.generateSuccessor(self.index, action)
    pos = successor.getAgentState(self.index).getPosition()
    if pos != nearestPoint(pos):  # Only half a grid position was covered
      return successor.generateSuccessor(self.index, action)
    else:
      return successor

  def rangeFoodCount(self, gameState, xrange, yrange):
    '''
    Computes how many foods in an area within xrange and yrange (e.g. xrange = range(1,10))
    '''

    foodcnt = 0
    for x in xrange:
      for y in yrange:
        if gameState.hasFood(x, y):
          foodcnt += 1
    return foodcnt

def getNeighbours(gameState, pos):
  """
  Given a position and current state, return all valid neighbouring coordinates
  and corresponding action.
  Parameters:
  ---------------
  gameState:
    current game state
  pos: tuple
    x, y coordinate: (x, y)
  Returns:
  ---------------
  neighbours: Dict
    a dictionary of which each key is a tuple of coordinate and corresponding value
    is an action(type: String).
  """
  x, y = pos
  up = (x, y+1); down = (x, y-1); left = (x-1, y); right = (x+1, y)
  neighbours = {}

  if not gameState.hasWall(up[0], up[1]):
    neighbours[up] = 'North'

  if not gameState.hasWall(down[0], down[1]):
    neighbours[down] = 'South'

  if not gameState.hasWall(left[0], left[1]):
    neighbours[left] = 'West'

  if not gameState.hasWall(right[0], right[1]):
    neighbours[right] = 'East'

  return neighbours

def getHomeBorder(gameState, red):
  width = gameState.data.layout.width
  height = gameState.data.layout.height
  halfway = width // 2
  y1 = 0
  y2 = height - 1
  redx1 = 0
  redx2 = halfway - 1
  bluex1 = halfway
  bluex2 = width - 1
  if red:
    return (redx1, redx2, y1, y2)
  else:
    return (bluex1, bluex2, y1, y2)


class SpecialPositions(object):
  """
  A class that memories the position of dead end, corridor and
  gate which leads to those two within a particular territory, and
  the number of food dots in each gate.
  """

  def __init__(self, gameState, isRed, mode, SmartAgent):
    self.state = gameState
    self.red = isRed
    self.mode = mode
    self.width = gameState.data.layout.width
    self.height = gameState.data.layout.height
    self.Agent = SmartAgent
    self.territory = self.getTerritory()
    self.food = self.getFood()  # determine which territory we are interested in
    self.coordInfoMap = {}  # mapping dictionary

  def getTerritory(self):
    if self.red:
      if self.mode == 'attack':
        return (range(self.width // 2, self.width-1), range(1, self.height-1))
      return (range(1, self.width // 2), range(1, self.height-1))
    else:
      if self.mode == 'attack':
        return (range(1, self.width // 2), range(1, self.height - 1))
      return (range(self.width // 2, self.width - 1), range(1, self.height - 1))

  def getFood(self):
    if self.mode == 'attack':
      return self.Agent.getFood(self, self.state)
    return self.Agent.getFoodYouAreDefending(self, self.state)


  def getDeadEndMap(self):
    """
    Returns a dictionary which maps from coordinate to some information,
    which is a dictionary containing whether it is labeled as 'D', label 'C',
    label 'G' and the number of food dot(s), where D, C, G stands for dead end,
    corridor and gate respectively.
    e.g. {'D': True, 'C': True, 'G': False, 'num_food': 2}
    The following layout returns {(x, y): {'D': True, 'C': False, 'G': False, 'num_food': 0},
    and if there is a food dot at coordinate D, return
    {(x, y): {'D': True, 'C': False, 'G': False, 'num_food': 1}
                              ----------·
                                       D|
                              ----------·
    """
    xrange, yrange = self.territory

    for x in xrange:
      for y in yrange:
        if not self.state.hasWall(x, y) and \
                len(getNeighbours(self.state, (x, y))) == 1:

          # primary information
          self.coordInfoMap[(x, y)] = {'D': True, 'C': False, 'G': False, 'food': set()}

          if self.food[x][y]:
            self.coordInfoMap[(x, y)]['food'].add((x, y))

    return self.coordInfoMap

  def mergeInfo(self, pos, neighbours):
    """
    A function which merges the information in each direction, including sum over all food
    dots and fix incorrect label Gate.
    e.g.                    ====
                        ===| D |
                        | D  G |
                        ===
      In the above layout, we need to update `num_food` in Gate position by incorporating
      information from two Dead-End positions.
    """
    for neighbour in neighbours:
      if neighbour not in self.coordInfoMap:
        continue
      if self.coordInfoMap[neighbour]['C'] or self.coordInfoMap[neighbour]['D']:
        self.coordInfoMap[neighbour]['G'] = False
        self.coordInfoMap[pos] = {'D': False, 'C': False, 'G': False, 'food': set()}
        self.coordInfoMap[pos]['food'] = self.coordInfoMap[pos]['food'].union(self.coordInfoMap[neighbour]['food'])
  def hasCorridorNearby(self, pos, neighbours):
    """
    A helper function which outputs whether there are enough corridors nearby given
    the current position and its neighbours to determine whether we stop expanding
    the next position.
    Parameters:
    ---------------
    pos: Tuple
      a tuple of x and y coordinate
    neighbours: List
      a list of tuples of neighbouring x and y coordinates
    Returns:
    ---------------
    a boolean variable of whether the position is a corridor
    """
    cnt = 0
    for neighbour in neighbours:
      if neighbour not in self.coordInfoMap:
        continue
      if self.coordInfoMap[neighbour]['C'] or self.coordInfoMap[neighbour]['D']:
        cnt += 1
    if cnt == len(neighbours) - 1:
      self.mergeInfo(pos, neighbours)
      return True
    return False

  def isCorridor(self, pos, neighbours):
    """
    Given the current position and its neighbours, return whether it is a
    corridor label.
    Parameters:
    ---------------
    pos: Tuple
      a tuple of x and y coordinate
    neighbours: List
      a list of tuples of neighbouring x and y coordinates
    Returns:
    ---------------
    a boolean variable of whether the position is a corridor
    """
    # case 1: one neighbour, return True
    if len(neighbours) == 1:
      self.coordInfoMap[pos] = {'D': False, 'C': False, 'G': False, 'food': set()}
      return True
    # case 2: two or three neighbours
    if len(neighbours) == 2 or len(neighbours) == 3:
      # return True if one or two of them is(are) labeled as 'D' or 'C'
      if self.hasCorridorNearby(pos, neighbours):
        return True
      return False

  def getNextPos(self, neighbours):
    """
    Output a valid neighbour. In this case, it only returns one that is not in
    self.coordInfoMap dictionary.
    """
    for neighbour in neighbours:
      if neighbour not in self.coordInfoMap:
        return neighbour

  def getCorridorAndGateMap(self):
    """
    Returns a dictionary which maps from coordinate to some information,
    which is a dictionary containing whether it is labeled as 'D', label 'C',
    label 'G' and the number of food dot(s), where D, C, G stands for dead end,
    corridor and gate respectively.
    e.g. the following layout is the expected return of label for each coordinate
                              -----------·
                              G C C C C D|
                              -----------·
    """

    coordInfoMap = self.getDeadEndMap().copy()

    for pos in coordInfoMap.keys():

      neighbours = list(getNeighbours(self.state, pos).keys())  # get all neighbours
      cur_pos = pos  # current position

      # expand nodes until Gate position is found
      while not self.coordInfoMap[cur_pos]['G']:
        next_pos = self.getNextPos(neighbours)  # next position
        if not next_pos:
          break
        neighbours = list(getNeighbours(self.state, next_pos).keys())
        neighbours.remove(cur_pos)  # next position's neighbours except the current position

        if self.isCorridor(next_pos, neighbours):
          self.coordInfoMap[next_pos]['C'] = True
          self.coordInfoMap[next_pos]['food'] = \
            self.coordInfoMap[next_pos]['food'].union(self.coordInfoMap[cur_pos]['food'].copy())
          if self.food[next_pos[0]][next_pos[1]]:
            self.coordInfoMap[next_pos]['food'].add(next_pos)
          cur_pos = next_pos
        else:
          self.coordInfoMap[cur_pos]['G'] = True
    return self.coordInfoMap

  def getDeadEndSet(self):
    coordInfoMap = self.getCorridorAndGateMap().copy()
    dead_end_set = set()

    for coord, info in coordInfoMap.items():
      if info['D']:
        dead_end_set.add(coord)
    return dead_end_set

  def getGateFoodDict(self):
    coordInfoMap = self.getCorridorAndGateMap().copy()
    gate_food_dict = {}
    for coord, info in coordInfoMap.items():
      if info['G']:
        gate_food_dict[coord] = info['food']

    return gate_food_dict

  def getCorridorSet(self):
    coordInfoMap = self.getCorridorAndGateMap().copy()
    corridor_set = set()

    for coord, info in coordInfoMap.items():
      if info['C']:
        corridor_set.add(coord)
    return corridor_set

# hyperparameters
blankHomeScore = -1  # living reward at home territory
blankEnemyScore = 1  # living reward at enemy territory
foodScore = 100  # reward for a single food dot
capsuleScore = 500  # reward for a capsule
ghostScore = -10000  # reward when there is a ghost
pacmanScore = 10000  # reward when there is a pacman


class Node(object):
  """
  A class that represents nodes in Monte Carlo Tree
  """
  def __init__(self, location):
    self.children = []
    self.parent = None
    self.action = None  # which action leads to this node
    self.value = 0  # q value
    self.reward = 0  # reward of a state
    self.num_visits = 0  # number of visits
    self.location = location  # state position

class MCTS(object):

  def __init__(self, gameState, index, rewardMap):
    self.gameState = gameState
    self.red = True if index in [0, 2] else False
    self.index = index
    self.rewardMap = rewardMap  # static reward map not including ghosts
    self.location = gameState.getAgentPosition(self.index)
    self.root = Node(self.location)
    self.closed = [self.root.location]  # the node we have visited before
    self.episode = 1000  # number of episode
    self.depth = 20  # maximum depth when doing simulation
    self.tree_depth = 0  # current tree depth, root node is 0
    self.tree_depth_thres = 5  # maximum tree depth
    self.epsilon = 0.1  # ϵ-greedy parameter
    self.gamma = 0.9  # discounted factor

  def getReward(self, gameState, myindex, pos):
    """
    This function returns a real-value reward including ghosts in some grids
    Parameters:
    ----------------
    gameState:
      current game state
    myindex: int
      agent index
    pos: tuple
      the coordinate of a position
    Returns:
    ----------------
    a real-value reward, which can be retrieved from `reward_dict` or manually
    assigned based on different conditions.
    """
    reward_dict = self.rewardMap  # reward map in SmartAgent.getRewardMap
    opponentIndices = [1, 3] if self.red else [0, 2]  # get opponent indices
    my_state = gameState.getAgentState(myindex)

    for enemy in opponentIndices:
      enemy_state = gameState.getAgentState(enemy)

      if enemy_state.getPosition():  # has enemies near by
        if pos == enemy_state.getPosition(): # `pos` overlaps with enemy position
          if enemy_state.isPacman:
            # if we are scared, return negated `pacmanScore`
            return pacmanScore if my_state.scaredTimer == 0 else -pacmanScore
          else:
            # if enemy ghost is scared, return 0
            return ghostScore if enemy_state.scaredTimer == 0 else 0

    return reward_dict[pos]

  def mctsSearch(self):
    """
    Returns a best action after doing Monte Carlo tree search, including
    4 steps: selection, expansion, simulation and backpropagation.
    """
    episode = 0  # current episode
    while episode < self.episode:
      leaf = self.traverse(self.root)  # selection
      self.rollout(leaf)  # expansion and simulation
      self.backprop(leaf)  # backpropagation
      episode += 1
    best_action = self.choose_best(self.root)  # choose an action with maximum q value
    return best_action

  def choose_best(self, root):
    """
    Choose an action with the maximum q value, by comparing children's
    attribute: `value`.
    Parameters:
    ----------------
    root: Class Node
      root node of Monte Carlo tree
    Returns:
    ----------------
    best_action: str
      an action with maximum q value
    """
    best_action = None; max_q = -float('inf')
    for child in root.children:
      if child.value >= max_q:
        max_q = child.value
        best_action = child.action
    return best_action

  def backprop(self, node):
    """
    Starting from the leaf node, backpropagate reward to its predecessor by
    the formula: V(s) = R(s) + γ·max_a' Q(s', a') where s is predecessor state
    and s' is successor state. For Q(s, a), we use flat Monte Carlo to update
    q value.
    Parameters:
    ---------------
    node: Class Node
      leaf node of the tree
    """
    while node:
      max_q = -float('inf')
      # choose the best child
      for child in node.children:
        if child.value > max_q:
          max_q = child.value
      value = node.value

      node.value = node.reward + self.gamma * max_q  # update rule
      node.value = (value * node.num_visits + node.value) / (node.num_visits + 1)  # flat Monte Carlo
      node.num_visits += 1  # increment the number of visit of a node
      node = node.parent


  def expand(self, pos, action, parent):
    """
    Expand a node based on information given(`pos`, `action` and `parent`),
    by instantiate a new node, then add the location into closed list `self.closed`.
    Parameters:
    ----------------
    pos: tuple
      a tuple of coordinate of a position
    action: str
      which action leads to this node
    parent: Class Node
      parent node
    Returns:
    ----------------
    node: Class Node
      a node with information
    """
    node = Node(pos)
    node.action = action
    node.reward = self.getReward(self.gameState, self.index, pos)
    parent.children.append(node)
    node.parent = parent
    self.closed.append(node.location)
    return node

  def simulate(self, node):
    """
    Starting from a node, randomly pick a successor, and calculate
    accumulated discounted reward. Note that the successor cannot be
    selected when it is already in `closed`.
    Parameters:
    -----------------
    node: Class Node
      node for simulation
    Returns:
    -----------------
    discounted_reward: float
      accumulated discounted reward starting from `node`
    """
    cur_pos = node.location
    t = 0; discounted_reward = 0
    closed = self.closed.copy()
    while t < self.depth:
      closed.append(cur_pos)
      r_t = self.getReward(self.gameState, self.index, cur_pos)
      discounted_reward += self.gamma ** t * r_t
      # terminate state
      if r_t == ghostScore:
        break
      cand_pos = list(getNeighbours(self.gameState, cur_pos))
      cand_pos = [pos for pos in cand_pos if pos not in closed]
      if not cand_pos:
        break
      cur_pos = random.choice(cand_pos)
      t += 1
    node.num_visits += 1
    return discounted_reward

  def rollout(self, leaf):
    """
    Expand all possible nodes, add them into `self.closed` and randomly pick
    a node for simulation
    Parameters:
    ----------------
    leaf: Class Node
      leaf node for simulation
    """
    neighbours = getNeighbours(self.gameState, leaf.location)
    expanded_nodes = []
    for pos, action in neighbours.items():
      if pos not in self.closed:
        expanded_nodes.append(self.expand(pos, action, leaf))

    # no expanded node, do simulation from `leaf` node
    if not expanded_nodes:
      expanded_nodes.append(leaf)

    # select a node randomly for simulation
    node_sim = random.choice(expanded_nodes)
    reward = self.simulate(node_sim)  # future reward
    node_sim.value = node_sim.reward + self.gamma * reward

  def epsilonGreedyPolicy(self, parent):
    """
    Choose a successor node with the maximum q value of probability
    1 - ϵ, and randomly pick the rest of them with probability ϵ.
    """
    children = parent.children
    max_q = -float('inf'); best_child = None
    # find a child node with the maximum q value
    for child in children:
      if child.value >= max_q:
        max_q = child.value
        best_child = child

    # if only one child available, do not do epsilon greedy
    if len(children) == 1:
      return best_child

    # epsilon-greedy
    children_copy = children.copy()
    children_copy.remove(best_child)  # remove the best one

    if random.random() < self.epsilon:
      return random.choice(children)

    # for random policy
    # return random.choice(children)

    return best_child

  def traverse(self, root):
    """
    Find the leaf node recursively, until it is indeed a leaf node, or
    exceed the threshold tree depth. Otherwise, invoke `epsilonGreedyPolicy` to
    get child node.
    """
    if not root.children:
      return root
    if self.tree_depth >= self.tree_depth_thres:
      return root
    child = self.epsilonGreedyPolicy(root)
    self.tree_depth += 1
    return self.traverse(child)