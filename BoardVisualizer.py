import pygame
import GameBoard
from sys import exit

BLACKCELLCOLOUR = (115,149,82)
WHITECELLCOLOUR = (235,236,208)
CELLSIZE = 100
BLACKMOVECOLOUR = (176,39,47)
WHITEMOVECOLOUR = (222,61,75)
PROMOTIONBOXCOLOUR = (255,255,255)
PROMOTIONCLOSECOLOUR = (241,241,241)

class GamePiece(pygame.sprite.Sprite):
    def __init__(self, rank, file, pieceType : int):
        super().__init__()
        self.__type = 0

        if GameBoard.Piece.isColour(pieceType, GameBoard.Piece.BLACK):
            imageName = "Dark"
            self.__type |= GameBoard.Piece.BLACK.value
        else:
            imageName = "Light"
            self.__type |= GameBoard.Piece.WHITE.value

        match GameBoard.Piece.pieceType(pieceType):
            case GameBoard.Piece.PAWN.value:
                imageName += "Pawn.png"
                self.__type |= GameBoard.Piece.PAWN.value
            case GameBoard.Piece.KING.value:
                imageName += "King.png"
                self.__type |= GameBoard.Piece.KING.value
            case GameBoard.Piece.KNIGHT.value:
                imageName += "Knight.png"
                self.__type |= GameBoard.Piece.KNIGHT.value
            case GameBoard.Piece.BISHOP.value:
                imageName += "Bishop.png"
                self.__type |= GameBoard.Piece.BISHOP.value
            case GameBoard.Piece.ROOK.value:
                imageName += "Rook.png"
                self.__type |= GameBoard.Piece.ROOK.value
            case GameBoard.Piece.QUEEN.value:
                imageName += "Queen.png"
                self.__type |= GameBoard.Piece.QUEEN.value
            case _:
                raise ValueError("Unknown Piece Type")
            
        self.image = pygame.transform.scale(pygame.image.load(f"pieces\{imageName}"), (CELLSIZE, CELLSIZE))
        self.rect = self.image.get_rect()
        self.setPos(rank, file)

    def setPos(self, rank=None, file=None):
        if rank is not None:
            self.__rank = rank
            self.rect.y = (7 - rank) * CELLSIZE
        if file is not None:
            self.__file = file
            self.rect.x = file * CELLSIZE
    
    def getPos(self):
        return (self.__rank, self.__file)
    
    def getType(self):
        return self.__type

class BoardVisualizer(GameBoard.Board):
    def __init__(self, FEN=None):
        super().__init__(FEN)
        self.screen = pygame.display.set_mode((CELLSIZE*8,CELLSIZE*8))
        pygame.display.set_caption("Chess!")
        self.clock = pygame.time.Clock()

        self.canShowMoves = True
        self.choosingPromotions = False
        self.showingPieceMove = None
        self.promotionRects = None

        self.renderBaseBoard(False)
        self.pieceList = self.initPieces()
        self.pieceList.draw(self.screen)
        pygame.display.update()

    def renderBaseBoard(self, update=True):
        rectList = []
        for file in range(8):
            for rank in range(8):
                cellColour = WHITECELLCOLOUR if (file + rank) % 2 == 0 else BLACKCELLCOLOUR
                rectList.append(pygame.draw.rect(self.screen, cellColour, (CELLSIZE * file, CELLSIZE * rank, CELLSIZE, CELLSIZE)))
        if update:
            pygame.display.update(rectList)

    def initPieces(self):
        pieceList = pygame.sprite.Group()
        for rank, row in enumerate(self.board):
            for file, cell in enumerate(row):
                if cell != 0:
                    newPiece = GamePiece((7 - rank), file, cell)
                    pieceList.add(newPiece)
            
        return pieceList

    def displayMoves(self, piece : GamePiece):
        if not GameBoard.Piece.isColour(piece.getType(), self.colourToMove):
            return

        self.curMoveList = self.moveGenerator(piece.getType(), piece.getPos())
        if self.curMoveList is None:
            return

        moveRectList = []
        for move in self.curMoveList:
            assert isinstance(move, GameBoard.Move)
            rank, file = move.getTarget()
            cellColour = BLACKMOVECOLOUR if ((file + rank) % 2 == 0) else WHITEMOVECOLOUR
            moveRectList.append(pygame.draw.rect(self.screen, cellColour, (CELLSIZE * file, CELLSIZE * (7 - rank), CELLSIZE, CELLSIZE)))

        
        self.pieceList.draw(self.screen)
        pygame.display.update()

        return moveRectList
    
    def resetDisplayedMoves(self):
        self.renderBaseBoard(False)

    def displayPromotions(self, newPos, oldPos):
        rectList = []
        file = newPos[1]
        for x in range(4):
            rectList.append(pygame.draw.rect(self.screen, PROMOTIONBOXCOLOUR, (CELLSIZE * file, CELLSIZE * x, CELLSIZE, CELLSIZE)))

        self.promotionGroup = pygame.sprite.Group()
        pieceColour = GameBoard.Piece.WHITE.value if GameBoard.Piece.isColour(self.getBoardValue(oldPos), GameBoard.Piece.WHITE) else GameBoard.Piece.BLACK.value

        for x in range(3, 7):
            self.promotionGroup.add(GamePiece(10-x, file, pieceColour + x))

        self.promotionGroup.draw(self.screen)
        pygame.display.update()

        return rectList


    def run(self):
        while self.gameState == 0:
            self.eventHandler()

            self.clock.tick(60)

        match self.gameState:
            case 1:
                pygame.display.set_caption("Draw!")
            case 2:
                pygame.display.set_caption("White wins!")
            case 3:
                pygame.display.set_caption("Black wins!")

        while True:
            self.checkGameClosed()
            self.clock.tick(60)

    def resetToMoveSelection(self):
        self.resetDisplayedMoves()
        self.pieceList.draw(self.screen)
        pygame.display.update()

        self.canShowMoves = True
        self.choosingPromotions = False
        self.showingPieceMove = None
        self.promotionRects = None

    def selectPiece(self, event):
        for piece in self.pieceList:
            assert isinstance(piece, GamePiece)
            if piece.rect.collidepoint(event.pos):
                self.moveRectList = self.displayMoves(piece)
                if self.moveRectList:
                    self.canShowMoves = False
                    self.showingPieceMove = piece

    def selectMove(self, event):
        for cell in self.moveRectList:
            assert isinstance(cell, pygame.Rect)
            assert isinstance(self.showingPieceMove, GamePiece)

            if cell.collidepoint(event.pos):
                if move := self.getMatchingMove(cell):
                    if move.type == GameBoard.MoveType.PROMOTION:
                        self.selectPromotingMove(move)
                        return
                    
                    elif move.type == GameBoard.MoveType.CASTLING:
                        self.selectCastling(move)
                    
                    elif self.getBoardValue(move.getTarget()): #There's a piece on the place we're moving to
                        self.selectCapture(move)

                    elif move.type == GameBoard.MoveType.ENPASSANT:
                        self.selectEnPassant(move)

                        
                    self.confirmMove(move)
                    self.showingPieceMove.setPos(move.getTarget()[0],move.getTarget()[1])
                    break

                break #No move selected

    def getMatchingMove(self, clickedCell : pygame.Rect) -> GameBoard.Move:
        for move in self.curMoveList:
            if move.getTarget() == (7 - (clickedCell.y // CELLSIZE), clickedCell.x // CELLSIZE):
                return move
        return None #No move clicked

    def selectPromotingMove(self, move : GameBoard.Move):
        self.promotionRects = self.displayPromotions(move.getTarget(), move.getOriginal())
        self.promotionMove = move
        self.choosingPromotions = True
        self.showingPieceMove = None

    def selectCastling(self, move : GameBoard.Move):
        for y in self.pieceList:
            assert isinstance(y, GamePiece)
            match move.getTarget():
                case (0,6): #White king side castle
                    if y.getPos() == (0,7):
                        y.setPos(0,5)
                        break
                case (0,2): #White queen side castle
                    if y.getPos() == (0,0):
                        y.setPos(0,3)
                        break
                case (7,6): #Black king side castle
                    if y.getPos() == (7,7):
                        y.setPos(7,5)
                        break
                case (7,2): #Black queen side castle
                    if y.getPos() == (7,0):
                        y.setPos(7,3)
                        break

    def selectCapture(self, move : GameBoard.Move):
        for y in self.pieceList:
            assert isinstance(y, GamePiece)
            if y.getPos() == move.getTarget():
                y.kill()
                del y
                break

    def selectEnPassant(self, move : GameBoard.Move):
        if self.colourToMove == GameBoard.Piece.WHITE:
            for y in self.pieceList:
                assert isinstance(y, GamePiece)
                if y.getPos() == (move.getTarget()[0] - 1, move.getTarget()[1]):
                    y.kill()
                    del y
                    break
        else:
            for y in self.pieceList:
                assert isinstance(y, GamePiece)
                if y.getPos() == (move.getTarget()[0] + 1, move.getTarget()[1]):
                    y.kill()
                    del y
                    break

    def selectPromotion(self, event):
        for promotionCell in self.promotionRects:
            move = self.promotionMove
            assert isinstance(promotionCell, pygame.Rect)
            assert isinstance(move, GameBoard.Move)
            if promotionCell.collidepoint(event.pos):
                pieceVal = 3 + (promotionCell.y // CELLSIZE)
                promoteTo = GameBoard.Piece.typeFromtInt(pieceVal)
                self.confirmMove(GameBoard.Move(move.getOriginal(), move.getTarget(), self.getBoardValue(move.getTarget()), GameBoard.MoveType.PROMOTION, promoteTo))
                for y in self.pieceList:
                    assert isinstance(y, GamePiece)
                    if y.getPos() == move.getOriginal():
                        y.kill()
                        del y
                        break

                self.pieceList.add(GamePiece(move.getTarget()[0], move.getTarget()[1], pieceVal))

    def eventHandler(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()

            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.canShowMoves:
                    self.selectPiece(event)
                    return
                        
                elif self.showingPieceMove:
                    self.selectMove(event)                    
                
                elif self.choosingPromotions:
                    self.selectPromotion(event)
                    
                # Did not return, so user did something that puts it back into original state
                self.resetToMoveSelection()

    def checkGameClosed(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                exit()




if __name__ == "__main__":
    # "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1"
    game = BoardVisualizer("rnb1k1nr/pppp1ppp/5q2/2b1p3/1P2P3/P7/2PP1PPP/RNB1KBNR b KQkq e3 0 1")
    game.run()