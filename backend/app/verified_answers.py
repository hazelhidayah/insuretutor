"""Reviewed answers for conditions that the bilingual extraction splits across columns."""

from dataclasses import dataclass
from hashlib import sha256
import re
import unicodedata

from .retrieval import RetrievedChunk, RetrievalStore


@dataclass(frozen=True)
class ReviewedClause:
    questions: frozenset[str]
    page: int
    sources: tuple[tuple[str, str], ...]
    section: str
    excerpt_anchor: str
    answers: dict[str, str]

    def evidence(self, store: RetrievalStore) -> list[RetrievedChunk]:
        verified = []
        for chunk_id, expected_hash in self.sources:
            chunk = store.public_passage(chunk_id)
            if chunk is None or chunk.page != self.page or sha256(chunk.text.encode("utf-8")).hexdigest() != expected_hash:
                return []
            verified.append(chunk)
        first = verified[0]
        return [RetrievedChunk(
            first.id, first.source, first.page, self.section,
            first.text[first.text.index(self.excerpt_anchor):], first.score,
        )]


COOLING_OFF = ReviewedClause(
    questions=frozenset({
        "保单的冷静期是多少天", "保单冷静期是多少天", "冷静期是多少天", "冷静期有多长",
        "保单冷静期从哪一天开始计算", "冷静期从哪一天开始算", "冷静期从什么时候开始",
        "保單的冷靜期是多少天", "保單冷靜期從哪一天開始計算",
        "how long is the cooling-off period", "when does the cooling-off period start",
        "how much time do i have to cancel my policy",
    }),
    page=15,
    sources=(
        ("prime-saver-p15-c3", "1d672bce6058777a0a38d893337d846730bd4c2ba78a061c52a46ed997b9b8cb"),
        ("prime-saver-p15-c2", "4971d91317e66ff0683e4b99cdb829df06d0a128df6888f173c6b7eef66e5fd2"),
    ),
    section="Cooling-off Period and Right of Cancellation / 保單冷靜期及取消保單的權利",
    excerpt_anchor="於交付保單的21個曆日內",
    answers={
        "en": "The insurer must receive your written cancellation request within 21 calendar days after the earlier of two events: delivery of the policy, or delivery of the notice that the policy is available for collection. The delivery can be to you or your representative. [S1]",
        "zh-CN": "冷静期为21个历日。从交付保单之日，或向您或您的代表交付可领取保单的通知书之日起计算，以较早者为准。保险公司须在这21个历日内收到书面取消申请。[S1]",
        "zh-TW": "冷靜期為21個曆日。從交付保單之日，或向您或您的代表交付可領取保單的通知書之日起計算，以較早者為準。保險公司須在這21個曆日內收到書面取消申請。[S1]",
    },
)

WITHDRAWALS = ReviewedClause(
    questions=frozenset({
        "定期提款有什么条件", "定期提款有哪些条件", "定期提款有什麼條件", "定期提款有甚麼條件",
        "我能定期取钱吗", "我能定期取錢嗎",
    }),
    page=12,
    sources=(
        ("prime-saver-p12-c3", "6c0e8b7377658249492b3319ec87adc7141261aefaf77dd4f099b82ed6c00e61"),
        ("prime-saver-p12-c2", "ddc6e04f3383cbcfdc32cc0a77341d28cd1e65365a2a6d6d4fffcc977ed92229"),
    ),
    section="Notes, item 6 / 附註第6項",
    excerpt_anchor="6. Automatic periodic withdrawal option",
    answers={
        "en": "Automatic periodic withdrawals are available once the policy has been in force for at least 10 years. The withdrawal charge is waived. [S1]\n\nUnder the brochure’s stated terms, monthly withdrawals have a minimum amount of US$500, HK$4,000 or MOP4,000 and a minimum term of one year. Annual withdrawals have a minimum amount of US$6,000, HK$48,000 or MOP48,000 and a minimum term of three years. Changes after confirmation incur a fee. [S1]",
        "zh-CN": "保单须已生效至少10年，才能使用自动定期提款。这项安排可免收提款费。[S1]\n\n按产品册所列条件，每月提款最低为500美元、4,000港元或4,000澳门元，提款期限最短一年。每年提款最低为6,000美元、48,000港元或48,000澳门元，提款期限最短三年。确认后更改安排须付手续费。[S1]",
        "zh-TW": "保單須已生效至少10年，才能使用自動定期提款。這項安排可免收提款費。[S1]\n\n按產品冊所列條件，每月提款最低為500美元、4,000港元或4,000澳門元，提款期限最短一年。每年提款最低為6,000美元、48,000港元或48,000澳門元，提款期限最短三年。確認後更改安排須付手續費。[S1]",
    },
)

PREMIUM_PAUSE = ReviewedClause(
    questions=frozenset({
        "can i stop paying premiums temporarily", "can i pause premium payments",
        "我可以暂停交保费吗", "我可以暫停交保費嗎",
    }),
    page=10,
    sources=(
        ("prime-saver-p10-c2", "e1a53cda2413a50fe4bada11c7713ba6525b016e5ed9fc99d00c2f790f7f427e"),
        ("prime-saver-p10-c1", "c426b2222dbc1c57bdcb8bc06834ed456f1a5c3165909b3427b60c52ad65fdf6"),
    ),
    section="Financial Flexibilities, Skip Premium Payments / 提存彈性，暫停繳付保費",
    excerpt_anchor="Cash withdrawal, reducing the premium amount, or skipping premium payments",
    answers={
        "en": "The brochure says you can temporarily skip premium payments if the policy has accumulated enough cash value. Monthly charges still apply. Skipping payments affects the cash value the policy accumulates. If the cash value cannot cover the monthly charges, the policy lapses with zero value. [S1]",
        "zh-CN": "根据产品册，如果保单已累积足够的现金价值，您可以暂停缴付保费。暂停缴费会影响现金价值的累积，每月费用仍会扣除。如果现金价值不足以支付每月费用，保单将终止且没有任何价值。[S1]",
        "zh-TW": "根據產品冊，如果保單已累積足夠的現金價值，您可以暫停繳付保費。暫停繳費會影響現金價值的累積，每月費用仍會扣除。如果現金價值不足以支付每月費用，保單將終止且沒有任何價值。[S1]",
    },
)

CLAUSES = (COOLING_OFF, WITHDRAWALS, PREMIUM_PAUSE)
COOLING_FOLLOW_UPS = frozenset({
    "那从哪一天开始算", "那從哪一天開始算", "那从什么时候开始算", "when does it start",
})


def _question_key(question: str) -> str:
    normalized = " ".join(unicodedata.normalize("NFKC", question).casefold().split())
    return re.sub(r"^(?:请问|請問)\s*", "", normalized).strip(" ?.!。")


def reviewed_clause(question: str, previous_question: str) -> ReviewedClause | None:
    key = _question_key(question)
    if key in COOLING_FOLLOW_UPS and _question_key(previous_question) in COOLING_OFF.questions:
        return COOLING_OFF
    return next((clause for clause in CLAUSES if key in clause.questions), None)
