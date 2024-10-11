from enum import Enum

'''
TODO:
- Implement castling
- Implement checks
'''

class MoveType(Enum):
    NORMAL = 0
    CASTLING = 1
    ENPASSANT = 2
    PROMOTION = 3

class Piece(Enum):
    #Rightmost 3 bits denote the piece type
    NONE = 0
    PAWN = 1
    KING = 2 #0b011
    KNIGHT = 3 #0b010

    #Sliding piece have their third bit 1
    BISHOP = 4 #0b110
    ROOK = 5 #0b100
    QUEEN = 6 #0b101

    #4th bit and 5th bit denote the piece colour
    WHITE = 8
    BLACK = 16

    #6th bit denotes if it has moved yet. Only used for king and rook
    #Depracated
    INITIALD = 32

    def pieceType(piece : int) -> int:
        return piece & 0b000111

    def pieceColour(piece : int) -> int:
        return piece & 0b011000

    def isSliding(piece : int) -> bool:
        return (piece >> 2) % 2
    
    def isType(piece : int, type : Enum) -> bool:
        return (piece & 0b000111) == type.value
    
    def isColour(piece : int, type : Enum) -> bool:
        return (piece & 0b011000) == (type.value)
    
    #depracated
    def isInitalD(piece : int) -> bool:
        return piece >> 5
    
    #depracated
    def removeIntialD(piece : int) -> int:
        return piece & 0b011111
    
    def flipColour(type : Enum) -> Enum:
        return Piece.WHITE if type == Piece.BLACK else Piece.BLACK
    
    def changePieceColour(pieceVal : int) -> int:
        return 0b011000 ^ pieceVal
    
    def typeFromtInt(piece : int) -> Enum:
        match Piece.pieceType(piece):
            case Piece.PAWN.value:
                return Piece.PAWN
            case Piece.KING.value:
                return Piece.KING
            case Piece.KNIGHT.value:
                return Piece.KNIGHT
            case Piece.BISHOP.value:
                return Piece.BISHOP
            case Piece.ROOK.value:
                return Piece.ROOK
            case Piece.QUEEN.value:
                return Piece.QUEEN
            case _:
                raise ValueError("Unknown piece")

class Move():
    def __init__(self, originalCell, destinationCell, targetValue, type : MoveType = MoveType.NORMAL, promotion : Piece = None, initialMove : bool = False):
        self.__original = originalCell
        self.__target = destinationCell
        self.__targetValue = targetValue
        self.type = type
        self.initialMove = initialMove
        if promotion:
            if self.type == MoveType.PROMOTION:
                self.promotion = promotion
            else:
                raise ValueError("promotion argument should only exist when MoveType is promotion")
    
    def getOriginal(self):
        return self.__original
    
    def getTarget(self):
        return self.__target
    
    def getTargetValue(self):
        return self.__targetValue

    def __repr__(self) -> str:
        return f"Move:\nOriginal Cell {self.getOriginal()}\nTarget Cell {self.getTarget()}\nCapturing {self.getTargetValue()}"

class Board():
    def __init__(self, initialState=None):
        if initialState == None:
            initialState = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
        self.board, whiteToMove, castling, self.enPassant, self.halfMove, self.fullMove = self.renderFEN(initialState)
        self.wKingCastle, self.bKingCastle, self.wQueenCastle, self.bQueenCastle = castling
        self.colourToMove = Piece.WHITE if whiteToMove else Piece.BLACK
        self.whitePieces, self.blackPieces = self.findAllPiecePositions()
        self.gameState = 0 #0 Running. 1 if draw, 2 if white win, 3 if black win

        self.wKingMoved = False
        self.bKingMoved = False
        self.wKRookMoved = False
        self.wQRookMoved = False
        self.bKRookMoved = False
        self.bQRookMoved = False
    
    def renderFEN(self, FEN : str):
        """Takes a FEN String and returns the data it represents

        Parameters:
        FEN (str): The FEN String representing the state of the board

        Returns:
        (board, whiteToMove, castleAvailability, enPassant, halfMove, fullMove)

        """
        board = [[0 for x in range(8)] for y in range(8)]
        pieceFromChar = {"p" : Piece.PAWN, "n" : Piece.KNIGHT, "b" : Piece.BISHOP, "r" : Piece.ROOK, "q" : Piece.QUEEN, "k" : Piece.KING}

        positioning, turn, castling, enPassant, halfMove, fullMove = FEN.split(" ")

        curRank = 8
        curFile = 0
        for char in positioning:
            if char.isnumeric():
                curFile += int(char)
            elif char == "/": # / Means new rank in FEN
                curFile = 0
                curRank -= 1
            else:
                newPiece = Piece.WHITE.value if char.isupper() else Piece.BLACK.value #If char is upper case, it is a white piece, else black
                
                try:
                    newPiece += pieceFromChar[char.lower()].value
                except KeyError:
                    raise ValueError(f"Invalid FEN String - Invalid piece placement: {FEN}")
                board[8 - curRank][curFile] = newPiece
                curFile += 1

        if curRank != 1 and curFile != 8: #If by the end of the positioning, check if curRank and curFile indicate end of board
            raise ValueError(f"Invalid FEN String - Invalid piece placement: {FEN}")
        
        if turn == "w":
            whiteToMove = True
        elif turn == "b":
            whiteToMove = False
        else:
            raise ValueError (f"Invalid FEN String - Active colour invalid: {FEN}")
        
        if castling == "-":
            castleAvailability = (False, False, False, False) #Unable to castle any direction for both sides
        else:
            castleAvailability = [False, False, False, False]
            for char in castling:
                match char:
                    case "k": #Black king-side castling available
                        castleAvailability[2] = True
                    case "K": #White king-side castling available
                        castleAvailability[0] = True
                    case "q": #Black queen-side castling available
                        castleAvailability[1] = True
                    case "Q": #White queen-side castling available
                        castleAvailability[3] = True
                    case _:
                        raise ValueError (f"Invalid FEN String - Castling availability invalid: {FEN}")
        
        if enPassant == "-":
            enPassant = None
        else:
            try:
                enPassant = Board.algebraicNotationToRankFile(enPassant)
            except ValueError:
                raise ValueError (f"Invalid FEN String - En Passant invalid: {FEN}")

        return (board, whiteToMove, castleAvailability, enPassant, halfMove, fullMove)
    
    def findAllPiecePositions(self) -> tuple[dict]:
        blackPieces = {Piece.PAWN: set(), Piece.KNIGHT: set(), Piece.BISHOP: set(), Piece.ROOK: set(), Piece.QUEEN: set(), Piece.KING : set()}
        whitePieces = {Piece.PAWN: set(), Piece.KNIGHT: set(), Piece.BISHOP: set(), Piece.ROOK: set(), Piece.QUEEN: set(), Piece.KING : set()}
        for rank, row in enumerate(self.board):
            for file, cell in enumerate(row):
                match Piece.pieceColour(cell):
                    case Piece.WHITE.value:
                        whitePieces[Piece.typeFromtInt(cell)].add((7-rank, file))
                    case Piece.BLACK.value:
                        blackPieces[Piece.typeFromtInt(cell)].add((7-rank, file))

        return (whitePieces, blackPieces)
        
    def moveGenerator(self, piece : int, position : tuple[int, int]):
        assert isinstance(piece, int)
        assert isinstance(position, tuple)
        if not Piece.isColour(piece, self.colourToMove): #Checks if piece is belongs to the current player's turn
            return None

        if Piece.isSliding(piece):
            moveList = self.__moveGeneratorHelper(piece, position, 8)
            return moveList
        
        match Piece.pieceType(piece):
            case Piece.PAWN.value: #Pawn
                moveList = self.__moveGeneratorPawn(piece, position)
            case Piece.KNIGHT.value: #Knight
                moveList = self.__moveGeneratorHelper(piece, position, repeat=1)
            case Piece.KING.value: #King
                moveList = self.__moveGeneratorHelper(piece, position, repeat=1) #repeat=1 so that only a movement distance of 1 is generated

                #Castling
                if not self.curKingThreat(): #Can only castle if king is not in check
                    if Piece.isColour(piece, Piece.WHITE):
                        if self.wKingCastle:
                            for move in moveList:
                                if (0,5) == move.getTarget() and self.getBoardValue((0,6)) == 0 and not self.threatChecker((0,6), Piece.WHITE): #Space directly next to king is safe+empty && castle target is empty && castle target is safe
                                    moveList.add(Move(position, (0,6), 0, MoveType.CASTLING, initialMove=True))
                                    break
                        if self.wQueenCastle:
                            for move in moveList:
                                if (0,3) == move.getTarget() and self.getBoardValue((0,2)) == 0 and not self.threatChecker((0,2), Piece.WHITE): #Space directly next to king is safe+empty && castle target is empty && castle target is safe
                                    moveList.add(Move(position, (0,2), 0, MoveType.CASTLING, initialMove=True))
                                    break
                    else:
                        if self.bKingCastle:
                            for move in moveList:
                                if (7,5) == move.getTarget() and self.getBoardValue((7,6)) == 0 and not self.threatChecker((7,6), Piece.BLACK): #Space directly next to king is safe+empty && castle target is empty && castle target is safe
                                    moveList.add(Move(position, (7,6), 0, MoveType.CASTLING, initialMove=True))
                                    break
                        if self.bQueenCastle:
                            for move in moveList:
                                if (7,5) == move.getTarget() and self.getBoardValue((7,6)) == 0 and not self.threatChecker((7,6), Piece.BLACK): #Space directly next to king is safe+empty && castle target is empty && castle target is safe
                                    moveList.add(Move(position, (7,2), 0, MoveType.CASTLING, initialMove=True))
                                    break
            case _:
                raise ValueError("Unknown piece")

        return moveList

    def __moveGeneratorHelper(self, piece, position, repeat=8):
        if Piece.isType(piece, Piece.KNIGHT):
            offsets = ((-2,-1), (-2,1), (-1,-2), (-1,2),
                       (1,-2), (1, 2), (2, 1), (2, -1)) #Offsets for knight movement
        else:
            offsets = ((-1,-1),(-1,1),(1, -1),(1, 1), #Offsets for diagonal moving pieces
                        (-1,0), (0, -1), (0, 1), (1, 0)) #Offsets for orthogonal moving pieces
        
        startIndex = 4 if Piece.isType(piece, Piece.ROOK) else 0 #If it's a rook, we only use the offsets for orthogonal pieces (offsets[4:])
        stopIndex = 4 if Piece.isType(piece, Piece.BISHOP) else 8 #If it's a bishop we only use the offsets for diagonal pieces (offests[:4])

        moveList = set()

        initialMove = False
        match Piece.typeFromtInt(piece):
            case Piece.KING:
                if Piece.isColour(piece, Piece.WHITE):
                    initialMove = not self.wKingMoved
                else:
                    initialMove = not self.bKingMoved
            case Piece.ROOK:
                if Piece.isColour(piece, Piece.WHITE):
                    if position[1] == 7: #King side rook
                        initialMove = not self.wKRookMoved
                    elif position[1] == 0: #Queen side rook
                        initialMove = not self.wQRookMoved
                else:
                    if position[1] == 7: #King side rook
                        initialMove = not self.bKRookMoved
                    elif position[1] == 0: #Queen side rook
                        initialMove = not self.bQRookMoved
        for x in range(startIndex, stopIndex):
            multiplier = 1

            while multiplier <= repeat:
                change = offsets[x]
                newPos = Board.posChange(position, change, multiplier)

                if Board.isOutOfBounds(newPos) or Piece.isColour(self.getBoardValue(newPos), self.colourToMove):
                    break

                if not self.curKingThreat(newMove := Move(position, newPos, self.getBoardValue(newPos), initialMove=initialMove)):
                    moveList.add(newMove)

                if Piece.isColour(self.getBoardValue(newPos), Piece.flipColour(self.colourToMove)):
                    break

                multiplier += 1

        return moveList
    
    def __moveGeneratorPawn(self, piece, position):
        offset  = ((1,0), (1,-1), (1,1), # White movement + capture
                   (-1,0), (-1,-1), (-1,1)) # Black movement + capture
        
        startIndex = 0 if Piece.isColour(piece, Piece.WHITE) else 3

        moveList = set()
        
        change = offset[startIndex]
        newPos = Board.posChange(position, change)
        if self.getBoardValue(newPos) == 0: #Empty Cell
            if not self.curKingThreat(Move(position, newPos, 0)):
                if (newPos[0] == 7 and Piece.isColour(piece, Piece.WHITE)) or (newPos[0] == 0 and Piece.isColour(piece, Piece.BLACK)):
                    moveList.add(Move(position, newPos, 0, MoveType.PROMOTION, Piece.BISHOP))
                    moveList.add(Move(position, newPos, 0, MoveType.PROMOTION, Piece.KNIGHT))
                    moveList.add(Move(position, newPos, 0, MoveType.PROMOTION, Piece.ROOK))
                    moveList.add(Move(position, newPos, 0, MoveType.PROMOTION, Piece.QUEEN))
                else:
                    moveList.add(Move(position, newPos, 0))

            #If double move is possible
            if (position[0] == 1 and Piece.isColour(piece, Piece.WHITE)) or (position[0] == 6 and Piece.isColour(piece, Piece.BLACK)):
                newPos2 = Board.posChange(newPos, change)
                if self.getBoardValue(newPos2) == 0 and not self.curKingThreat(Move(position, newPos2, 0)): #Empty Cell 2 spaces
                    moveList.add(Move(position, newPos2, 0))
                    self.enPassant = newPos
        
        #Captures
        for change in offset[startIndex+1], offset[startIndex+2]:
            newPos = Board.posChange(position, change)
            
            #If diagonal movement lands on a piece of different colour
            if Board.isOutOfBounds(newPos):
                continue

            if Piece.isColour(self.getBoardValue(newPos), Piece.flipColour(self.colourToMove)):
                if not self.curKingThreat(Move(position, newPos, self.getBoardValue(newPos))):
                    if (newPos[0] == 7 and Piece.isColour(piece, Piece.WHITE)) or (newPos[0] == 0 and Piece.isColour(piece, Piece.BLACK)):
                        moveList.add(Move(position, newPos, self.getBoardValue(newPos), MoveType.PROMOTION, Piece.BISHOP))
                        moveList.add(Move(position, newPos, self.getBoardValue(newPos), MoveType.PROMOTION, Piece.KNIGHT))
                        moveList.add(Move(position, newPos, self.getBoardValue(newPos), MoveType.PROMOTION, Piece.ROOK))
                        moveList.add(Move(position, newPos, self.getBoardValue(newPos), MoveType.PROMOTION, Piece.QUEEN))
                    else:
                        moveList.add(Move(position, newPos, self.getBoardValue(newPos)))
                
            #En passant
            if self.getBoardValue(newPos) == 0 and newPos == self.enPassant and not self.curKingThreat(Move(position, newPos, self.getBoardValue(newPos), MoveType.ENPASSANT)):
                moveList.add(Move(position, newPos, self.getBoardValue(newPos), MoveType.ENPASSANT))


        return moveList

    def generateAllMoves(self, colour : Piece) -> dict:
        moveList = {}
        if colour == Piece.WHITE:
            for pieces in self.whitePieces.values():
                for piecePos in pieces:
                    moveList[piecePos] = self.moveGenerator(self.getBoardValue(piecePos), piecePos)
        elif colour == Piece.BLACK:
            for pieces in self.blackPieces.values():
                for piecePos in pieces:
                    moveList[piecePos] = self.moveGenerator(self.getBoardValue(piecePos), piecePos)
        else:
            raise ValueError("Unknown colour")
        return moveList
    
    def curKingThreat(self, move = None) -> bool:
        #Looping just in case you play a weird mode with multiple kings
        for x in self.getCurrentColourPieces()[Piece.KING]:
            if self.threatChecker(x, self.colourToMove, move):
                return True
        return False

    def threatChecker(self, pos : tuple[int, int], allyColour : Enum, move : Move = None) -> bool:
        '''
        Checks if there is a piece threatening the cell pos
        if move is provided, evaluate the threat after move has been made
        returns True if there is a threat, false if not
        '''
        offsets = ((-1,-1),(-1,1),(1, -1),(1, 1), #Offsets for diagonal moving pieces
                    (-1,0), (0, -1), (0, 1), (1, 0)) #Offsets for orthogonal moving pieces
        knightOffset = ((-2,-1), (-2,1), (-1,-2), (-1,2),
                       (1,-2), (1, 2), (2, 1), (2, -1))
        pawnOffset = ((1,-1),(1,1), #White pawn captures
                     (-1,-1), (-1,1)) #Black pawn capturess

        if move:
            #If we're tracking the threat to the king
            if Piece.isType(self.getBoardValue(move.getOriginal()), Piece.KING):
                pos = move.getTarget()
            self.__makeMove(move)

        #Knight threats
        for x in knightOffset:
            newPos = Board.posChange(pos, x)
            if not(Board.isOutOfBounds(newPos)) and (self.getBoardValue(newPos) == (Piece.flipColour(allyColour).value + Piece.KNIGHT.value)):
                if move:
                    self.unmakeMove(move)
                return True
        
        #Sliding Pieces and king threat
        for x in range(0, 7):
            multiplier = 1

            while multiplier <= 7: #Guaranteed out of bounds if multiplier is > 8
                change = offsets[x]
                newPos = Board.posChange(pos, change, multiplier)

                if Board.isOutOfBounds(newPos) or Piece.isColour(newPosPiece := self.getBoardValue(newPos), allyColour):
                    break

                if Piece.isColour(newPosPiece, Piece.flipColour(allyColour)):
                    if Piece.isType(newPosPiece, Piece.QUEEN) or Piece.isType(newPosPiece, (Piece.BISHOP if x <= 3 else Piece.KNIGHT)) or (Piece.isType(newPosPiece, Piece.KING) and multiplier == 1):
                        if move:
                            self.unmakeMove(move)
                        return True
                    else:
                        break

                multiplier += 1

        #Pawns
        startIndex = 0 if allyColour == Piece.BLACK else 2
        for x in range(startIndex, startIndex+2):
            newPos = Board.posChange(pos, pawnOffset[x])

            if Board.isOutOfBounds(newPos) or Piece.isColour(newPosPiece := self.getBoardValue(newPos), allyColour):
                continue
            
            if newPosPiece == (allyColour.value + Piece.PAWN.value): #Check if it is a opposing pawn
                if move:
                    self.unmakeMove(move)
                return True

        if move:
            self.unmakeMove(move)
        return False

    def confirmMove(self, move : Move):
        self.__makeMove(move)
        for x in self.generateAllMoves(self.colourToMove).values():
            if x:
                return #Found a move
        

        #No moves found
        if self.curKingThreat():
            self.gameState = 2 if self.colourToMove == Piece.BLACK else 3
        else:
            self.gameState = 1


    
    def __makeMove(self, move : Move):
        originalPos = move.getOriginal()
        target = move.getTarget()
        movingPiece = self.getBoardValue(originalPos)
        currentColourPieces = self.getCurrentColourPieces()
        oppositeColourPieces = self.getOppositeColourPieces()

        if move.type == MoveType.PROMOTION:
            currentColourPieces[Piece.PAWN].remove(originalPos) #Remove pawn
            if capturedPiece := move.getTargetValue():
                oppositeColourPieces[Piece.typeFromtInt(capturedPiece)].remove(target) #Remove target
            currentColourPieces[move.promotion].add(target) #Add promoted piece

            self.setBoardValue(move.promotion.value, move.getTarget())
            self.setBoardValue(0, originalPos)

            self.colourToMove = Piece.flipColour(self.colourToMove)
            return
        
        #Disabling Castling
        match Piece.typeFromtInt(movingPiece):
            case Piece.KING:
                if self.colourToMove == Piece.WHITE:
                    self.wKingMoved = True
                    self.wKingCastle, self.wQueenCastle = False, False
                else:
                    self.bKingMoved = True
                    self.bKingCastle, self.bQueenCastle = False, False
            case Piece.ROOK:
                rookFile = move.getOriginal()[1]
                if self.colourToMove == Piece.WHITE:
                    if rookFile == 7:
                        self.wKRookMoved = True
                        self.wKingCastle = False
                    elif rookFile == 0:
                        self.wQRookMoved = True
                        self.wQueenCastle = False
                else:
                    if rookFile == 7:
                        self.bKRookMoved = True
                        self.bKingCastle = False
                    elif rookFile == 0:
                        self.bQRookMoved = True
                        self.bKingCastle = False

        #Setting board values when castling
        if move.type == MoveType.CASTLING:
            currentColourPieces[Piece.KING].remove(originalPos)
            currentColourPieces[Piece.KING].add(target)
            
            rank = target[0]
            match target[1]:
                case 6: #King side castle
                    currentColourPieces[Piece.ROOK].remove((rank, 7))
                    currentColourPieces[Piece.ROOK].add((rank, 5))

                    self.setBoardValue(0, (rank, 7))
                    self.setBoardValue(Piece.ROOK.value + self.colourToMove.value, (rank, 5))
                case 2: #Queen side castle
                    currentColourPieces[Piece.ROOK].remove((rank, 0))
                    currentColourPieces[Piece.ROOK].add((rank, 3))

                    self.setBoardValue(0, (rank, 0))
                    self.setBoardValue(Piece.ROOK.value + self.colourToMove.value, (rank, 3))
                case _:
                    raise ValueError("Castling target is wrong")

            self.setBoardValue(movingPiece, target)
            self.setBoardValue(0, originalPos)

            self.colourToMove = Piece.flipColour(self.colourToMove)
            return
    
        #Setting board values for any other case
        currentColourPieces[Piece.typeFromtInt(movingPiece)].remove(originalPos)
        currentColourPieces[Piece.typeFromtInt(movingPiece)].add(target)

        #If there is a captured piece, remove it from known piece list
        if capturedPiece := move.getTargetValue():
            try:
                oppositeColourPieces[Piece.typeFromtInt(capturedPiece)].remove(target)
            except Exception:
                print(move)
                raise Exception
            
        self.setBoardValue(movingPiece, target)
        self.setBoardValue(0, originalPos)

        self.colourToMove = Piece.flipColour(self.colourToMove)


    def unmakeMove(self, move : Move):
        self.colourToMove = Piece.flipColour(self.colourToMove)

        originalPos = move.getOriginal()
        target = move.getTarget()
        movingPiece = self.getBoardValue(target)
        currentColourPieces = self.getCurrentColourPieces()
        oppositeColourPieces = self.getOppositeColourPieces()

        if move.initialMove:
            match Piece.pieceType(movingPiece):
                case Piece.KING.value:
                    if self.colourToMove == Piece.WHITE:
                        self.bKingMoved = False
                        if not self.bKRookMoved:
                            self.bKingCastle = True
                        if not self.bQRookMoved:
                            self.bQueenCastle = True
                    else:
                        self.wKingMoved = False
                        if not self.wKRookMoved:
                            self.wKingCastle = True
                        if not self.wQRookMoved:
                            self.wQueenCastle = True
                case Piece.ROOK.value:
                    if originalPos[1] == 0: #Queen side rook
                        if self.colourToMove == Piece.WHITE:
                            self.bQRookMoved = False
                            if not self.bKingMoved:
                                self.bQueenCastle = True
                        else:
                            self.wQRookMoved = False
                            if not self.wKingMoved:
                                self.wQueenCastle = True

                    elif originalPos[1] == 7: #King side rook
                        if self.colourToMove == Piece.WHITE:
                            self.bKRookMoved = False
                            if not self.bKingMoved:
                                self.bKingCastle = True
                        else:
                            self.wKRookMoved = False
                            if not self.wKingMoved:
                                self.wKingCastle = True

                case _:
                    raise ValueError("Only rooks/kings will have initial move")

        if move.type == MoveType.PROMOTION:
            currentColourPieces[move.promotion].remove(target)
            currentColourPieces[Piece.PAWN].add(originalPos)
            if capturedPiece := move.getTargetValue():
                oppositeColourPieces[Piece.typeFromtInt(capturedPiece)].add(target)

            self.setBoardValue(Piece.PAWN + Piece.pieceColour(move.getTargetValue()), originalPos)
            self.setBoardValue(move.getTargetValue(), target)
            return

        if move.type == MoveType.CASTLING:
            currentColourPieces[Piece.KING].remove(target)
            currentColourPieces[Piece.KING].add(originalPos)
            
            rank = target[0]
            match target[1]:
                case 6: #King side castle
                    currentColourPieces[Piece.ROOK].remove(rank, 5)
                    currentColourPieces[Piece.ROOK].add(rank, 7)

                    self.setBoardValue(Piece.ROOK.value + self.colourToMove.value + Piece.INITIAL.value, (rank, 7))
                    self.setBoardValue(0, (rank, 5))
                case 2: #Queen side castle
                    currentColourPieces[Piece.ROOK].remove(rank, 3)
                    currentColourPieces[Piece.ROOK].add(rank, 0)

                    self.setBoardValue(Piece.ROOK.value + self.colourToMove.value + Piece.INITIAL.value, (rank, 0))
                    self.setBoardValue(0, (rank, 3))
                case _:
                    raise ValueError("Castling target is wrong")

            self.setBoardValue(movingPiece, originalPos)
            self.setBoardValue(movingPiece, originalPos)
            return

        currentColourPieces[Piece.typeFromtInt(movingPiece)].remove(target)
        currentColourPieces[Piece.typeFromtInt(movingPiece)].add(originalPos)
        if capturedPiece := move.getTargetValue():
            oppositeColourPieces[Piece.typeFromtInt(capturedPiece)].add(target)

        self.setBoardValue(self.getBoardValue(target), originalPos)
        self.setBoardValue(move.getTargetValue(), target)

    def printBoard(self):
        for x in self.board:
            print(x)

    def getBoardValue(self, position) -> int:
        return self.board[7-position[0]][position[1]]
    
    def setBoardValue(self, value, position):
        self.board[7-position[0]][position[1]] = value

    def getCurrentColourPieces(self) -> dict:
        return self.blackPieces if self.colourToMove == Piece.BLACK else self.whitePieces
    
    def getOppositeColourPieces(self) -> dict:
        return self.whitePieces if self.colourToMove == Piece.BLACK else self.blackPieces
    
    def isOutOfBounds(position):
        return not(0 <= position[0] <= 7 and 0 <= position[1] <= 7)

    def algebraicNotationToRankFile(algebraic : str):
        """Takes a string in algebraic notation and returns the corresponding 0-indexed rank and file in the form (rank, file)"""
        fileMapping = {"a":0,"b":1,"c":2,"d":3,"e":4,"f":5,"g":6,"h":7}
        if len(algebraic) != 2:
            raise ValueError(f"Invalid algebraic notation {algebraic}")
        if not (algebraic[1].isnumeric() and 1 <= int(algebraic[1]) <= 8):
            raise ValueError(f"Invalid algebraic notation: {algebraic}")
        try:
            return (int(algebraic[1]) - 1, fileMapping[algebraic[0]])
        except KeyError:
            raise ValueError(f"Invalid algebraic notation: {algebraic}")
    
    def posChange(oldPos, change, multiplier=1):
        return (oldPos[0] + change[0] * multiplier, oldPos[1] + change[1] * multiplier)

if __name__=="__main__":
    # "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQK2R w KQkq - 0 1"
    game = Board("rnb1k1nr/pppp1ppp/5q2/2b1p3/1P2P3/P7/2PP2PP/RNBQKBNR b KQkq - 0 1")
    game.confirmMove(Move((5,5), (1,5), 0))
    pos = Board.algebraicNotationToRankFile("e1")
    print(pos)
    print(Piece.typeFromtInt(game.getBoardValue(pos)))
    temp = game.moveGenerator(game.getBoardValue(pos), pos)
    counter = 1
    if temp:
        for x in temp:
            print(x)
    else:
        print(game.gameState)
        print("No valid moves")