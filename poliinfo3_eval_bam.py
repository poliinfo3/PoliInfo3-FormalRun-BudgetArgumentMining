from __future__ import annotations

"""NTCIR-16 QA Lab-PoliInfo3 Budget Argument Miningタスクの自動評価スクリプト．
（一般配布用）

Python 3.8で動作確認済み。
Usage:
    python poliinfo3_eval_bam.py -g [path_to_gold_standard] -f [path_to_estimated]

author: OTOTAKE Hokuto
modified: 2021/11/09
"""
import argparse
import dataclasses
import json
import sys
from pathlib import Path
from typing import Optional, Union

VERSION = "20211027"


@dataclasses.dataclass(frozen=True)
class MoneyExpression:
    moneyExpression: str
    relatedID: Optional[Union[list[str], str]]  # 推定結果の場合はstrの場合がある、GSはリスト
    argumentClass: Optional[str]

    @property
    def argumentClassStr(self) -> str:
        return self.argumentClass if self.argumentClass is not None else ""


@dataclasses.dataclass(frozen=True)
class LProceedingItem:
    speakerPosition: str
    speaker: str
    utterance: str
    moneyExpressions: list[MoneyExpression]

    @staticmethod
    def from_dict(d: dict[str, any]):
        return LProceedingItem(
            speakerPosition=d["speakerPosition"],
            speaker=d["speaker"],
            utterance=d["utterance"],
            moneyExpressions=[MoneyExpression(**m) for m in d["moneyExpressions"]],
        )


@dataclasses.dataclass(frozen=True)
class LProceedingObject:
    date: str
    localGovernmentCode: str
    localGovernmentName: str
    proceedingTitle: str
    url: str
    proceeding: list[LProceedingItem]

    @staticmethod
    def from_dict(d: dict[str, any]):
        return LProceedingObject(
            date=d["date"],
            localGovernmentCode=d["localGovernmentCode"],
            localGovernmentName=d["localGovernmentName"],
            proceedingTitle=d["proceedingTitle"],
            url=d["url"],
            proceeding=[LProceedingItem.from_dict(x) for x in d["proceeding"]],
        )


@dataclasses.dataclass(frozen=True)
class DSpeechRecord:
    speechID: str
    speechOrder: int
    speaker: str
    speakerYomi: Optional[str]
    speakerGroup: Optional[str]
    speakerPosition: Optional[str]
    speakerRole: Optional[str]
    speech: str
    startPage: int
    createTime: str
    updateTime: str
    speechURL: str
    moneyExpressions: list[MoneyExpression]

    @staticmethod
    def from_dict(d: dict[str, any]):
        return DSpeechRecord(
            speechID=d["speechID"],
            speechOrder=d["speechOrder"],
            speaker=d["speaker"],
            speakerYomi=d["speakerYomi"],
            speakerGroup=d["speakerGroup"],
            speakerPosition=d["speakerPosition"],
            speakerRole=d["speakerRole"],
            speech=d["speech"],
            startPage=d["startPage"],
            createTime=d["createTime"],
            updateTime=d["updateTime"],
            speechURL=d["speechURL"],
            moneyExpressions=[MoneyExpression(**m) for m in d["moneyExpressions"]],
        )


@dataclasses.dataclass(frozen=True)
class DProceedingObject:
    issueID: str
    imageKind: str
    searchObject: int
    session: int
    nameOfHouse: str
    nameOfMeeting: str
    issue: str
    date: str
    closing: Optional[str]
    speechRecord: list[DSpeechRecord]
    meetingURL: str
    pdfURL: str

    @staticmethod
    def from_dict(d: dict[str, any]):
        return DProceedingObject(
            issueID=d["issueID"],
            imageKind=d["imageKind"],
            searchObject=d["searchObject"],
            session=d["session"],
            nameOfHouse=d["nameOfHouse"],
            nameOfMeeting=d["nameOfMeeting"],
            issue=d["issue"],
            date=d["date"],
            closing=d["closing"],
            speechRecord=[DSpeechRecord.from_dict(x) for x in d["speechRecord"]],
            meetingURL=d["meetingURL"],
            pdfURL=d["pdfURL"],
        )


@dataclasses.dataclass(frozen=True)
class MinutesObject:
    """
    BAMタスクにおける入力データのフォーマット．
    地方議会と国会の両方を持つ．
    """

    local: list[LProceedingObject]
    diet: list[DProceedingObject]

    @staticmethod
    def from_dict(d: dict[str, any]):
        return MinutesObject(
            local=[LProceedingObject.from_dict(x) for x in d["local"]],
            diet=[DProceedingObject.from_dict(x) for x in d["diet"]],
        )


class EvalInstance:
    argumentClassIsCorrectExactlyAndCorrectRelatedIdInclude: bool
    argumentClassIsCorrectExactly: bool
    argumentClassIsCorrect: bool
    numRelatedIdsGS: int
    numRelatedIdsTarget: int
    numRelatedIdsCorrect: int
    firstRelatedIdInGS: bool  # 推定relatedIDの1番目のIDがGSデータに含まれているか

    _acMap: dict[str, str] = {
        "Premise : 過去・決定事項": "Premise",
        "Premise : 未来（現在以降）・見積": "Premise",
        "Premise : その他（例示・訂正事項など）": "Premise",
        "Claim : 意見・提案・質問": "Claim",
        "Claim : その他": "Claim",
        "金額表現ではない": "その他",
        "その他": "その他",
    }

    def __init__(self, gs: MoneyExpression, target: MoneyExpression) -> None:
        def lenN(v: Optional[Union[str, list[str]]]) -> int:
            if v is None:
                return 0
            if isinstance(v, str):
                return 1
            return len(v)

        def setN(v: Optional[Union[str, list[str]]]) -> set[str]:
            if v is None:
                return set()
            if isinstance(v, str):
                return set([v])
            return set(v)

        def first(v: Union[str, list[str]]) -> str:
            if isinstance(v, str):
                return v
            return v[0]

        _d = EvalInstance._acMap
        self.argumentClassIsCorrectExactly = gs.argumentClass == target.argumentClass
        self.argumentClassIsCorrect = _d[gs.argumentClass] == _d.get(
            target.argumentClass, "その他"
        )
        self.numRelatedIdsGS = lenN(gs.relatedID)
        self.numRelatedIdsTarget = lenN(target.relatedID)
        self.numRelatedIdsCorrect = lenN(
            setN(gs.relatedID).intersection(setN(target.relatedID))
        )

        self.argumentClassIsCorrectExactlyAndCorrectRelatedIdInclude = False
        self.firstRelatedIdInGS = False
        if lenN(gs.relatedID) == 0 and lenN(target.relatedID) == 0:
            self.argumentClassIsCorrectExactlyAndCorrectRelatedIdInclude = (
                gs.argumentClass == target.argumentClass
            )
        elif lenN(gs.relatedID) > 0 and lenN(target.relatedID) > 0:
            if len(setN(gs.relatedID).intersection(setN(target.relatedID))) > 0:
                self.argumentClassIsCorrectExactlyAndCorrectRelatedIdInclude = (
                    gs.argumentClass == target.argumentClass
                )
            self.firstRelatedIdInGS = first(target.relatedID) in setN(gs.relatedID)

    def fScoreRelatedIds(self) -> Optional[float]:
        """
        relatedIDに関するF値を計算する。
        realtedIDの正解データがnullの場合は、計算対象外ということでNoneを返す。
        relatedIDの推定値がnullの場合は、0を返す。
        """
        if self.numRelatedIdsGS == 0:
            return None
        if self.numRelatedIdsTarget == 0:
            return 0
        p = self.numRelatedIdsCorrect / self.numRelatedIdsTarget
        r = self.numRelatedIdsCorrect / self.numRelatedIdsGS
        if p + r == 0:
            return 0
        return (2 * p * r) / (p + r)

    def acc(self) -> int:
        """
        argumentClassIsCorrectExactlyのときは1、それ以外は0を返す。
        """
        return 1 if self.argumentClassIsCorrectExactly else 0

    def ridc(self) -> int:
        """
        firstRelatedIdInGSのときは1、それ以外は0を返す。
        """
        return 1 if self.firstRelatedIdInGS else 0


@dataclasses.dataclass
class MexInstance:
    idx: tuple[int, int, int]
    gs: MoneyExpression
    target: Optional[MoneyExpression] = None
    evalobj: Optional[EvalInstance] = None

    def setTarget(self, target: MoneyExpression) -> bool:
        if self.gs.moneyExpression != target.moneyExpression:
            return False
        self.target = target
        return True

    def evaluate(self):
        self.evalobj = EvalInstance(self.gs, self.target)


class EvalCollection:
    numArgumentClassCorrectExactlyAndRelatedIdInclude: int
    numArgumentClassCorrectExactly: int
    numArgumentClassCorrect: int
    numArgumentClass: int
    numAcPremiseGS: int
    numAcPremiseTarget: int
    numAcPremiseCorrect: int
    numAcClaimGS: int
    numAcClaimTarget: int
    numAcClaimCorrect: int
    numRelatedIdsGS: int
    numRelatedIdsTarget: int
    numRelatedIdsCorrect: int

    numRelatedIdExistGS: int
    sumArgumentClassCorrectExactlyAndRelatedIdFscore: float
    numArgumentClassCorrectExactlyAndSingleRelatedIdInclude: int

    def __init__(self, mis: list[MexInstance] = []) -> None:
        self.numArgumentClassCorrectExactlyAndRelatedIdInclude = 0
        self.numArgumentClassCorrectExactly = 0
        self.numArgumentClassCorrect = 0
        self.numArgumentClass = 0
        self.numAcPremiseGS = 0
        self.numAcPremiseTarget = 0
        self.numAcPremiseCorrect = 0
        self.numAcClaimGS = 0
        self.numAcClaimTarget = 0
        self.numAcClaimCorrect = 0
        self.numRelatedIdsGS = 0
        self.numRelatedIdsTarget = 0
        self.numRelatedIdsCorrect = 0

        self.numRelatedIdExistGS = 0
        self.sumArgumentClassCorrectExactlyAndRelatedIdFscore = 0.0
        self.numArgumentClassCorrectExactlyAndSingleRelatedIdInclude = 0
        self.numSingleRelatedIdInclude = 0

        for mi in mis:
            self.numArgumentClass += 1
            self.numArgumentClassCorrectExactly += (
                mi.evalobj.argumentClassIsCorrectExactly
            )
            self.numArgumentClassCorrectExactlyAndRelatedIdInclude += (
                mi.evalobj.argumentClassIsCorrectExactlyAndCorrectRelatedIdInclude
            )
            self.numArgumentClassCorrect += mi.evalobj.argumentClassIsCorrect
            self.numAcPremiseGS += mi.gs.argumentClassStr.startswith("Premise")
            self.numAcPremiseTarget += mi.target.argumentClassStr.startswith("Premise")
            self.numAcPremiseCorrect += mi.gs.argumentClassStr.startswith(
                "Premise"
            ) and mi.target.argumentClassStr.startswith("Premise")
            self.numAcClaimGS += mi.gs.argumentClassStr.startswith("Claim")
            self.numAcClaimTarget += mi.target.argumentClassStr.startswith("Claim")
            self.numAcClaimCorrect += mi.gs.argumentClassStr.startswith(
                "Claim"
            ) and mi.target.argumentClassStr.startswith("Claim")
            self.numRelatedIdsGS += mi.evalobj.numRelatedIdsGS
            self.numRelatedIdsTarget += mi.evalobj.numRelatedIdsTarget
            self.numRelatedIdsCorrect += mi.evalobj.numRelatedIdsCorrect

            frid = mi.evalobj.fScoreRelatedIds()
            if frid is not None:
                self.numRelatedIdExistGS += 1
                self.sumArgumentClassCorrectExactlyAndRelatedIdFscore += (
                    mi.evalobj.acc() * frid
                )
                self.numArgumentClassCorrectExactlyAndSingleRelatedIdInclude += (
                    mi.evalobj.acc() * mi.evalobj.ridc()
                )
                self.numSingleRelatedIdInclude += mi.evalobj.ridc()

    def merge(self, other: EvalCollection) -> EvalCollection:
        ret = EvalCollection()
        ret.numArgumentClassCorrectExactly = (
            self.numArgumentClassCorrectExactly + other.numArgumentClassCorrectExactly
        )
        ret.numArgumentClassCorrectExactlyAndRelatedIdInclude = (
            self.numArgumentClassCorrectExactlyAndRelatedIdInclude
            + other.numArgumentClassCorrectExactlyAndRelatedIdInclude
        )
        ret.numArgumentClassCorrect = (
            self.numArgumentClassCorrect + other.numArgumentClassCorrect
        )
        ret.numArgumentClass = self.numArgumentClass + other.numArgumentClass
        ret.numAcPremiseGS = self.numAcPremiseGS + other.numAcPremiseGS
        ret.numAcPremiseTarget = self.numAcPremiseTarget + other.numAcPremiseTarget
        ret.numAcPremiseCorrect = self.numAcPremiseCorrect + other.numAcPremiseCorrect
        ret.numAcClaimGS = self.numAcClaimGS + other.numAcClaimGS
        ret.numAcClaimTarget = self.numAcClaimTarget + other.numAcClaimTarget
        ret.numAcClaimCorrect = self.numAcClaimCorrect + other.numAcClaimCorrect
        ret.numRelatedIdsGS = self.numRelatedIdsGS + other.numRelatedIdsGS
        ret.numRelatedIdsTarget = self.numRelatedIdsTarget + other.numRelatedIdsTarget
        ret.numRelatedIdsCorrect = (
            self.numRelatedIdsCorrect + other.numRelatedIdsCorrect
        )

        ret.numRelatedIdExistGS = self.numRelatedIdExistGS + other.numRelatedIdExistGS
        ret.sumArgumentClassCorrectExactlyAndRelatedIdFscore = (
            self.sumArgumentClassCorrectExactlyAndRelatedIdFscore
            + other.sumArgumentClassCorrectExactlyAndRelatedIdFscore
        )
        ret.numArgumentClassCorrectExactlyAndSingleRelatedIdInclude = (
            self.numArgumentClassCorrectExactlyAndSingleRelatedIdInclude
            + other.numArgumentClassCorrectExactlyAndSingleRelatedIdInclude
        )
        ret.numSingleRelatedIdInclude = (
            self.numSingleRelatedIdInclude + other.numSingleRelatedIdInclude
        )

        return ret

    def accuracyArgumentClassExactlyAndSingleRelatedIdInclude(self) -> float:
        return (
            self.numArgumentClassCorrectExactlyAndSingleRelatedIdInclude
            / self.numRelatedIdExistGS
        )

    def accuracyArgumentClassExactlyAndRelatedIdFscore(self) -> float:
        return (
            self.sumArgumentClassCorrectExactlyAndRelatedIdFscore
            / self.numRelatedIdExistGS
        )

    def accuracyArgumentClassExactlyAndRelatedIdInclude(self) -> float:
        return (
            self.numArgumentClassCorrectExactlyAndRelatedIdInclude
            / self.numArgumentClass
        )

    def accuracyArgumentClassExactly(self) -> float:
        return self.numArgumentClassCorrectExactly / self.numArgumentClass

    def accuracyArgumentClass(self) -> float:
        return self.numArgumentClassCorrect / self.numArgumentClass

    def precisionAcPremise(self) -> float:
        if self.numAcPremiseTarget == 0:
            return 0
        return self.numAcPremiseCorrect / self.numAcPremiseTarget

    def recallAcPremise(self) -> float:
        if self.numAcPremiseGS == 0:
            return 0
        return self.numAcPremiseCorrect / self.numAcPremiseGS

    def precisionAcClaim(self) -> float:
        if self.numAcClaimTarget == 0:
            return 0
        return self.numAcClaimCorrect / self.numAcClaimTarget

    def recallAcClaim(self) -> float:
        if self.numAcClaimGS == 0:
            return 0
        return self.numAcClaimCorrect / self.numAcClaimGS

    def precisionRelatedIds(self) -> float:
        if self.numRelatedIdsTarget == 0:
            return 0
        return self.numRelatedIdsCorrect / self.numRelatedIdsTarget

    def recallRelatedIds(self) -> float:
        if self.numRelatedIdsGS == 0:
            return 0
        return self.numRelatedIdsCorrect / self.numRelatedIdsGS

    def accuracySingleRelatedIdInclude(self) -> float:
        return self.numSingleRelatedIdInclude / self.numRelatedIdExistGS

    def to_dict(self) -> dict:
        return {
            "accuracy_ac_1rid_完全一致": self.accuracyArgumentClassExactlyAndSingleRelatedIdInclude(),
            "accuracy_ac_ridFscore_完全一致": self.accuracyArgumentClassExactlyAndRelatedIdFscore(),
            "accuracy_ac_rid_完全一致": self.accuracyArgumentClassExactlyAndRelatedIdInclude(),
            "accuracy_ac_完全一致": self.accuracyArgumentClassExactly(),
            "accuracy_ac": self.accuracyArgumentClass(),
            "precision_ac_Premise": self.precisionAcPremise(),
            "recall_ac_Premise": self.recallAcPremise(),
            "precision_ac_Claim": self.precisionAcClaim(),
            "recall_ac_Claim": self.recallAcClaim(),
            "precision_relatedID": self.precisionRelatedIds(),
            "recall_relatedID": self.recallRelatedIds(),
            "accuracy_1relatedID": self.accuracySingleRelatedIdInclude(),
        }


@dataclasses.dataclass
class MexObj:
    local: list[MexInstance]
    diet: list[MexInstance]

    evalLocal: Optional[EvalCollection] = None
    evalDiet: Optional[EvalCollection] = None
    evalAll: Optional[EvalCollection] = None

    def evaluate(self):
        self.evalLocal = EvalCollection(self.local)
        self.evalDiet = EvalCollection(self.diet)
        self.evalAll = self.evalLocal.merge(self.evalDiet)


def get_args():
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("-g", "--gs-data", required=True, help="GSデータを指定します")
    parser.add_argument("-f", "--input-file", required=True, help="入力データを指定します")
    parser.add_argument("-p", "--prettify", action="store_true")
    return parser.parse_args()


def load_gs(gs_path: str) -> MexObj:
    ret = MexObj(local=[], diet=[])
    p = Path(gs_path)
    obj = MinutesObject.from_dict(json.loads(p.read_text(encoding="utf-8-sig")))

    for i, pobj in enumerate(obj.local):
        for j, proc in enumerate(pobj.proceeding):
            for k, mex in enumerate(proc.moneyExpressions):
                ret.local.append(MexInstance(idx=(i, j, k), gs=mex))

    for i, dobj in enumerate(obj.diet):
        for j, record in enumerate(dobj.speechRecord):
            for k, mex in enumerate(record.moneyExpressions):
                ret.diet.append(MexInstance(idx=(i, j, k), gs=mex))

    return ret


def load_input(input_path: str, mexobj: MexObj):
    p = Path(input_path)
    obj = MinutesObject.from_dict(json.loads(p.read_text(encoding="utf-8-sig")))

    n = 0
    for i, pobj in enumerate(obj.local):
        for j, proc in enumerate(pobj.proceeding):
            for k, mex in enumerate(proc.moneyExpressions):
                if not mexobj.local[n].setTarget(mex):
                    raise Exception(
                        f"""金額表現の不一致エラーです．
地方議会会議録[{i+1}番目]:{pobj.localGovernmentCode}_{pobj.localGovernmentName}:{pobj.date}
発言[{j+1}番目]:発言者名_{proc.speaker}
金額表現[{k+1}番目]: {mex.moneyExpression}"""
                    )
                mexobj.local[n].evaluate()
                n += 1

    n = 0
    for i, dobj in enumerate(obj.diet):
        for j, record in enumerate(dobj.speechRecord):
            for k, mex in enumerate(record.moneyExpressions):
                if not mexobj.diet[n].setTarget(mex):
                    raise Exception(
                        f"""金額表現の不一致エラーです．
国会会議録[{i+1}番目]:issueID={dobj.issueID}
発言[{j+1}番目]:発言者名_{record.speaker}
金額表現[{k+1}番目]: {mex.moneyExpression}"""
                    )
                mexobj.diet[n].evaluate()
                n += 1


def main() -> str:
    args = get_args()

    # GS読込
    mexobj = load_gs(args.gs_data)

    # 評価対象読込，各インスタンスの評価
    load_input(args.input_file, mexobj)

    # 評価の集計
    mexobj.evaluate()

    # extra info
    extra_info = f"AC={mexobj.evalAll.accuracyArgumentClassExactly():.4f}, RID={mexobj.evalAll.accuracySingleRelatedIdInclude():.4f}"

    # 出力
    output = {
        "status": "success",
        "score": mexobj.evalAll.accuracyArgumentClassExactlyAndSingleRelatedIdInclude(),
        "version": VERSION,
        "extra_info": extra_info,
        "micro_ave": {
            "local": mexobj.evalLocal.to_dict(),
            "diet": mexobj.evalDiet.to_dict(),
            "all": mexobj.evalAll.to_dict(),
        },
    }
    if args.prettify:
        return json.dumps(output, ensure_ascii=False, indent=4)
    else:
        return json.dumps(output, ensure_ascii=False)


if __name__ == "__main__":
    # print(main())
    try:
        print(main())
    except Exception as e:
        tb = sys.exc_info()[2]
        print(e.with_traceback(tb), file=sys.stderr)
        print(json.dumps({"status": "failed", "message": str(e)}, ensure_ascii=False))
