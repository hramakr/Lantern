
"""
Lantern
Parse and convert Zork Muddle source code to different data structures.
"""


# input file
mudfile = 'data/mdl/dung.mud'

# output files
lispfile = 'data/lisp/zork.lisp'
jsonfile = 'data/json/zork.json'
graphvizfile = 'data/graphviz/zork.gv'


import mud # the MDL parser/compiler


# can add global variables here, though might be overwritten by
# setg and psetg commands in dung.mud.
# mud.global_env[',FOO'] = 42


# define special form functions, which will be added to the mudpy parser.
# in lisp these would be defined as macros.

def form_room(x, env):
    "ROOM special form handler"
    key, desc, name, exits = x[1:5] # unpack arguments
    # create a new environment with ROOM-KEY, to pass to the EXIT special form
    parms = ['ROOM-KEY']
    args = [key]
    newenv = mud.Env(parms, args, env)
    # evaluate values
    name = mud.eval(name, newenv) # need this in case name is a global variable reference
    desc = mud.eval(desc, newenv) # ditto
    exits = mud.eval(exits, newenv) # parse EXIT special form
    room = {'key': key, 'name': name, 'desc': desc, 'exits': exits}
    return room


def form_exit(x, env):
    "EXIT special form handler"
    # transform the special exits and return as an unconditional exit list
    if mud.debug: print 'exit',x
    exits = []
    tokens = x[1:]
    while tokens:
        token = tokens.pop(0) # pop from start of list
        if isinstance(token, mud.List):
            #> these should all be mud.eval calls
            if token[0] == 'CEXIT': # handle conditional exit form
                token = mud.eval(token) # replace CEXIT struct with a room key
            elif token[0] == 'DOOR': # handle door exit form
                # this will be token 2 or 3 - want the one other than the current room
                roomkey = env.findvalue('ROOM-KEY') # passed down from ROOM special form
                if mud.debug: print 'roomkey', roomkey
                if token[2] == roomkey:
                    token = token[3] # replace DOOR struct with a room key
                else:
                    token = token[2]
            elif token[0] == 'SETG':
                token = mud.eval(token) # replace SETG form with room key
        elif token == '#NEXIT': # no exit
            #> this should be handled at lexical level? ie #something wraps following form?
            # handle bug with room BKBOX - #NEXIT listed twice - pop it also
            if tokens[0] == '#NEXIT':
                tokens.pop(0)
            # remove following token, which is a no-exit string
            tokens.pop(0)
        elif token.startswith(','): #> eval should handle these
            val = mud.eval(token)
            if val is None:
                if mud.debug: print 'unknown/unparsed gvar',token
                val = token
            token = val
        exits.append(token)
    return exits


def form_cexit(x, env):
    "CEXIT special form handler"
    if mud.debug: print 'cexit',x
    # (_, cond, tform, fform, unk, fn) = x
    # we just want the tform
    tform = x[2]
    value = mud.eval(tform, env)
    return value


# def form_door(x, env):
#     "DOOR special form handler"
#     if mud.debug: print 'door',x
#     # this will be token 2 or 3 - want the one other than the current room
#     if token[2] == roomkey:
#         token = token[3] # replace DOOR struct with a room key
#     else:
#         token = token[2]
#     value = mud.eval(tform, env)
#     return value


def form_setg(x, env):
    "SETG special form handler"
    # set a global variable value to an evaluated form value and return that value.
    # can skip the setting part and just return the value for now.
    if mud.debug: print 'setg',x
    # (_, var, form) = x  # crashes if form is '#NEXIT'
    var = x[1]
    form = x[2]
    value = mud.eval(form, env)
    mud.global_env[',' + var] = value # set global variable value
    return value

# assign the special form functions to a dictionary in mudpy
mud.forms['room'] = form_room
mud.forms['exit'] = form_exit
mud.forms['cexit'] = form_cexit
mud.forms['setg'] = form_setg
mud.forms['psetg'] = form_setg # psetg calls setg and adds to a 'pure' list - not needed


if __name__=='__main__':

    s = """
    <ROOM "WHOUS"
    "This is an open field west of a white house, with a boarded front door."
           "West of House"
           <EXIT "NORTH" "NHOUS" "SOUTH" "SHOUS" "WEST" "FORE1"
                  "EAST" #NEXIT "The door is locked, and there is evidently no key.">
           (<GET-OBJ "FDOOR"> <GET-OBJ "MAILB"> <GET-OBJ "MAT">)
           <>
           <+ ,RLANDBIT ,RLIGHTBIT ,RNWALLBIT ,RSACREDBIT>
           (RGLOBAL ,HOUSEBIT)>
    <SETG KITCHEN-WINDOW <DOOR "WINDO" "KITCH" "EHOUS">>
    <ROOM "EHOUS"
           ""
           "Behind House"
           <EXIT "NORTH" "NHOUS" "SOUTH" "SHOUS" "EAST" "CLEAR"
                  "WEST" ,KITCHEN-WINDOW
                  "ENTER" ,KITCHEN-WINDOW>
           (<GET-OBJ "WINDO">)
           EAST-HOUSE
           <+ ,RLANDBIT ,RLIGHTBIT ,RNWALLBIT ,RSACREDBIT>
           (RGLOBAL ,HOUSEBIT)>
    <ROOM "LROOM"
           ""
           "Living Room"
           <EXIT "EAST" "KITCH"
                  "WEST" <CEXIT "MAGIC-FLAG" "BLROO" "The door is nailed shut.">
                  "DOWN" <DOOR "DOOR" "LROOM" "CELLA">>
           (<GET-OBJ "WDOOR"> <GET-OBJ "DOOR"> <GET-OBJ "TCASE">
            <GET-OBJ "LAMP"> <GET-OBJ "RUG"> <GET-OBJ "PAPER">
            <GET-OBJ "SWORD">)
           LIVING-ROOM
           <+ ,RLANDBIT ,RLIGHTBIT ,RHOUSEBIT ,RSACREDBIT>>
    <PSETG STFORE "This is a forest, with trees in all directions around you.">
    <PSETG FOREST "Forest">
    <PSETG FORDES
    "This is a dimly lit forest, with large trees all around.  To the
east, there appears to be sunlight.">
    <PSETG FORTREE
    "This is a dimly lit forest, with large trees all around.  One
particularly large tree with some low branches stands here.">
    <PSETG NOTREE #NEXIT "There is no tree here suitable for climbing.">
    <ROOM "FORE1"
           ,STFORE
           ,FOREST
           <EXIT "UP" ,NOTREE
                 "NORTH" "FORE1" "EAST" "FORE3" "SOUTH" "FORE2" "WEST" "FORE1">
           ()
           FOREST-ROOM
           <+ ,RLANDBIT ,RLIGHTBIT ,RNWALLBIT ,RSACREDBIT>
           (RGLOBAL <+ ,TREEBIT ,BIRDBIT ,HOUSEBIT>)>
    """

    # s = "<COND ((if 0 1 0) 3) (1 5)>"

    # s = """
    # <PSETG FOO "pokpok">
    # ,FOO
    # """

    # s = """
    # <PSETG FOO ["pokpok"]>
    # ,FOO
    # """
    # print mud.parse(s)

    mud.debug = False
    # mud.debug = True
    mud.compile = True


    f = open(mudfile)
    s = f.read()
    f.close()

    # program = "(begin " + s + ")"
    program = "(list " + s + ")"
    objs = mud.eval(mud.parse(program))
    rooms = [obj for obj in objs if isinstance(obj, dict)]

    roomlist = []
    exitlist = []

    for room in rooms:

        key = room['key']
        name = room['name']
        desc = room['desc']
        exits = room['exits']

        # output lisp structure
        # exits = ' '.join(room['exits'])
    #     s = """(room %s
    # (name %s)
    # (desc %s)
    # (exit %s))""" % (key, name, desc, exits)
    #     print s
    #     print


        # handle json structures
        tostr = lambda s: s[1:-1]

        key = tostr(key)
        name = tostr(name)
        desc = tostr(desc)

        o = {'key': key, 'name': name, 'desc': desc}
        roomlist.append(o)

        while exits:
            dir = exits.pop(0)
            target = exits.pop(0)
            dir = tostr(dir)
            target = tostr(target)
            o = {'source': key, 'dir': dir, 'target': target}
            exitlist.append(o)

    # output json structure
    objs = {'rooms': roomlist, 'exits': exitlist}
    import json
    print json.dumps(objs, indent=2)





