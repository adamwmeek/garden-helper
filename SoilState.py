from statemachine import StateMachine, State

class SoilState(StateMachine):

    preDamp = State("preDamp", initial = True)
    realDamp = State("realDamp")
    preDry = State("preDry")
    realDry = State("realDry")

    seeDampWhenPDamp = preDamp.to(realDamp)
    seeDryWhenPDamp = preDamp.to(preDry)

    seeDryWhenRDamp = realDamp.to(preDry)

    seeDampWhenPDry = preDry.to(preDamp)
    seeDryWhenPDry = preDry.to(realDry)

    seeDampWhenRDry = realDry.to(preDamp)



