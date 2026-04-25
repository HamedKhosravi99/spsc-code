&#x20; ## Chunk A2 — Claude



&#x20;(1) Lemma K\_inverse — VERIFIED



&#x20; Re-derivation via Isserlis:

&#x20; $$(\\mathcal K(M)){kl} = \\sum{ij} M\_{ij},\\E\[u\_iu\_ju\_ku\_l] =

&#x20; \\sum\_{ij}M\_{ij}(\\delta\_{ij}\\delta\_{kl}+\\delta\_{ik}\\delta\_{jl}+\\delta\_{il}\\delta\_{jk}) = \\tr(M)\\delta\_{kl} + M\_{kl} +

&#x20; M\_{lk}.$$

&#x20; Symmetric $M \\Rightarrow \\mathcal K(M)=2M+\\tr(M)I\_d$. Taking trace, $\\tr(\\mathcal K(M))=(d+2)\\tr(M)$, so inversion $M

&#x20; = N/2 - \\tr(N)/(2(d+2)),I\_d$ with $N=\\mathcal K(M)$ is exact. Operator norm: for symmetric $N$ with eigenvalues

&#x20; $\\lambda\_i$, eigenvalues of $\\mathcal K^{-1}(N)$ are $\\lambda\_i/2 - \\tr(N)/(2(d+2))$, bounded by $|N|/2 +

&#x20; d|N|/(2(d+2)) = \\frac{d+1}{d+2}|N| < |N|$. So $|\\mathcal K^{-1}|\_\\op = (d+1)/(d+2) < 1$. Claim $\\le 1$ holds with

&#x20; slack $1/(d+2)$.



&#x20; ---

&#x20; (2) Lemma quad\_conf — VERIFIED (with one exposition gap)



&#x20; $y\_t^2$ expansion is mechanical. Conditional on $\\sigma(\\cH\_{t-1}, u\_t)$, independence of $u\_t$ from $(\\theta\_t,

&#x20; \\cH\_{t-1})$ gives $\\E\[\\theta\_t\\theta\_t^\\top\\mid\\cH\_{t-1},u\_t] = \\widetilde M\_t$, so

&#x20; $\\E\[(u^\\top\\theta)^2\\mid\\cdot]=u^\\top\\widetilde M\_t u$. Middle term: $m\_t :=

&#x20; \\E\[\\varepsilon\_t\\theta\_t\\mid\\cH\_{t-1},u\_t] = \\E\[\\varepsilon\_t\\theta\_t\\mid\\cH\_{t-1}]$ by independence — not a function

&#x20; of $u\_t$. Noise term: uses $\\E\[\\varepsilon\_t^2\\mid\\cH\_{t-1},u\_t] = \\sigma\_\\varepsilon^2$.



&#x20; Exposition gaps (not fatal): (i) The setup states $|\\E\[\\varepsilon\_t\\theta\_t]|\\le\\epsilon\_\\times$ unconditionally, but

&#x20;  the proof needs $|\\E\[\\varepsilon\_t\\theta\_t\\mid\\cH\_{t-1}]|\\le\\epsilon\_\\times$ a.s. These are genuinely different;

&#x20; paper should restate assumption conditionally. (ii) "Sub-Gaussian with variance $\\sigma\_\\varepsilon^2$" is ambiguous;

&#x20; the derivation silently needs $\\E\[\\varepsilon\_t^2\\mid\\cH\_{t-1}] = \\sigma\_\\varepsilon^2$ exactly, which is a stronger

&#x20; conditional-variance assumption than sub-Gaussianity.



&#x20; ---

&#x20; (3) Lemma G\_unbiased — FLAGGED



&#x20; Step that fails (line 138 of the proof):



&#x20; ▎ $|\\E\[(u\_t^\\top m\_t)u\_tu\_t^\\top]|\\op \\le L\\epsilon\\times\\cdot L^2 = L^3\\epsilon\_\\times$



&#x20; Concrete counterexample to the derivation. Take $d=2$, $m\_t = (\\epsilon\_\\times, 0)^\\top$, and $u \\sim N(0, I\_2)$

&#x20; untruncated (as written — no $\\mathbf 1{\\cA\_t}$ appears in the definition of $G\_t$ or in the expectation). The

&#x20; inequality $|u^\\top m\_t| \\le |u||m\_t| \\le L\\epsilon\_\\times$ relies on $|u|\\le L$, but $|u|$ is unbounded with positive

&#x20;  probability. The stated "deterministic" chain is invalid.



&#x20; Correct computation: for any $\\cH\_{t-1}$-measurable fixed vector $m$ and $u \\sim N(0, I\_d)$,

&#x20; $$(\\E\[(u^\\top m)uu^\\top]){kl} = \\sum\_i m\_i,\\E\[u\_iu\_ku\_l] = 0$$

&#x20; by vanishing Gaussian third moments. So the middle term contributes exactly zero, and

&#x20; $$\\widetilde B\_t ;=; -\\delta\\sigma,\\mathcal K^{-1}(I\_d) ;=; -\\frac{\\delta\_\\sigma}{d+2},I\_d.$$

&#x20; True bound: $|\\widetilde B\_t|\\op = |\\delta\\sigma|/(d+2)$, a clean scaled identity.



&#x20; Stated bound $|\\delta\_\\sigma|L^2 + 2L^3\\epsilon\_\\times$: holds only trivially (as "nonnegative $\\ge 0$"), via a broken

&#x20;  chain of reasoning. Loose by factor $\\sim 2d(d+2)\\log(4T/\\delta)$.



&#x20; Similar issue with the $\\delta\_\\sigma$ term: "$|\\E\[u\_tu\_t^\\top]|\\op\\le L^2$" is false for untruncated Gaussian — the

&#x20; correct value is $|I\_d|\\op = 1$. Again the derivation invokes truncation that is not present in the lemma statement.



&#x20; Scaled-identity claim: correct under untruncated interpretation (and the parenthetical $(1-O(\\delta/T))$ caveat is

&#x20; unnecessary — no truncation correction appears because the lemma is untruncated).



&#x20; Impact: conclusion is salvageable as an upper bound; downstream rates inherit loose (but not wrong) $L^2, L^3$

&#x20; factors. The proof as written is not a proof.



&#x20; ---

&#x20; (4) Lemma G\_bound — VERIFIED (with $d=1$ constants nit)



&#x20; Observability: $\\mathbf 1{\\cA\_t}$ is $\\sigma(u\_t,y\_t)$-measurable ⇒ $\\cH\_t$-measurable, not $\\cH\_{t-1}$-measurable. ✓



&#x20; On $\\cA\_t$: $|s\_t| = |y\_t^2 - \\hat\\sigma^2| \\le L\_y^2 + \\hat\\sigma^2 = R\_s$; $|G\_t|\_\\op \\le |s\_t||u|^2 \\le R\_s L^2 \\le

&#x20;  R\_X$. The $+S\_w^2$ buffer in $R\_X$ is unnecessary for bounding $|G\_t|$ itself, but doesn't hurt. (The stated

&#x20; justification "absorbs the centering term" is incoherent for $G\_t$; it applies to $\\tilde X\_t$ in Thm 5.)



&#x20; Probability bound issue at $d=1$: with $L^2 = 2d\\log(4T/\\delta) = 2\\log(4T/\\delta)$ and $|u|\\sim|N(0,1)|$,

&#x20; $\\Pr(|u|>L)\\le 2e^{-L^2/2}=\\delta/(2T)$, not $\\delta/(4T)$ as claimed. Via Laurent–Massart the $\\delta/(4T)$ claim

&#x20; holds for $d\\ge 2$ (when $\\log(4T/\\delta)\\ge 2$). Final union-bound total $\\delta/(2T)+\\delta/(2T) = \\delta/T$ still

&#x20; holds for $d=1$, so the lemma's conclusion $\\Pr(\\cA\_t^c)\\le\\delta/T$ survives. Minor constant slip.



&#x20; ---

&#x20; (5) Theorem matrix\_bernstein\_conf — VERIFIED (with two caveats)



&#x20; MDS. $\\tilde G\_t = G\_t\\mathbf 1{\\cA\_t}$ is $\\cH\_t$-measurable; $\\tilde X\_t := \\tilde G\_t - \\E\[\\tilde

&#x20; G\_t\\mid\\cH\_{t-1}]$ has $\\E\[\\tilde X\_t\\mid\\cH\_{t-1}]=0$ by construction. ✓ Symmetric: $\\tilde G\_t$ is image of

&#x20; $\\mathcal K^{-1}$ of symmetric input, so Hermitian in the real sense. ✓



&#x20; a.s. bound. $|\\tilde G\_t|\\op \\le R\_X$ a.s. (on $\\cA\_t^c$ it's 0; on $\\cA\_t$ it's $\\le R\_s L^2 \\le R\_X$). By Jensen for

&#x20;  the operator norm, $|\\E\[\\tilde G\_t\\mid\\cH{t-1}]|\_\\op \\le R\_X$. So $|\\tilde X\_t|\\le 2R\_X$. ✓



&#x20; Predictable variance. $\\tilde G\_t$ symmetric with $|\\tilde G\_t|\\le R\_X$ ⇒ $-R\_X I\\preceq \\tilde G\_t \\preceq R\_X I$ ⇒

&#x20; $\\tilde G\_t^2 \\preceq R\_X^2 I$, so $\\E\[\\tilde G\_t^2\\mid\\cH\_{t-1}]\\preceq R\_X^2 I$. And $\\E\[\\tilde X\_t^2\\mid\\cH\_{t-1}]

&#x20; = \\E\[\\tilde G\_t^2\\mid\\cH\_{t-1}] - (\\E\[\\tilde G\_t\\mid\\cH\_{t-1}])^2 \\preceq R\_X^2 I$ (subtracting PSD). Summed:

&#x20; $\\lambda\_{\\max}(\\sum\\E\[\\tilde X\_t^2\\mid\\cH\_{t-1}])\\le m\_k R\_X^2$ by PSD sum. ✓



&#x20; Bernstein inversion. With per-term bound $2R\_X$ and total variance $m\_k R\_X^2$, inverting $2d\\exp(-r^2/(2m\_k R\_X^2 +

&#x20; 4R\_X r/3))\\le\\delta$ via $\\sqrt{a+b}\\le\\sqrt a+\\sqrt b$:

&#x20; $$r \\le \\frac{2R\_X\\log(2d/\\delta)}{3} + R\_X\\sqrt{2m\_k\\log(2d/\\delta)}.$$

&#x20; Dividing by $m\_k$: $R\_X\\sqrt{2\\log(2d/\\delta)/m\_k} + 2R\_X\\log(2d/\\delta)/(3m\_k)$. The paper's coefficient

&#x20; $2R\_X\\sqrt{\\log(2d/\\delta)/m\_k}$ is looser (by $\\sqrt 2$) but valid; the $2R\_X\\log(2d/\\delta)/(3m\_k)$ matches. ✓



&#x20; Transfer identity. On $\\cE=\\bigcap\_t\\cA\_t$: $\\tilde G\_t=G\_t$ ⇒ $\\bar{\\tilde G}k=\\widehat M\_k$. $\\E\[\\tilde

&#x20; G\_t\\mid\\cH{t-1}] = \\E\[G\_t\\mid\\cH\_{t-1}] - \\E\[G\_t\\mathbf 1{\\cA\_t^c}\\mid\\cH\_{t-1}] = \\widetilde M\_t+\\widetilde B\_t -

&#x20; (\\Theta\_k$ contribution$)$. Algebra: $\\widehat M\_k - \\bar M\_k^{\\text{probe}} - \\widetilde B = m\_k^{-1}\\sum\\tilde X\_t -

&#x20;  \\Theta\_k$ on $\\cE$. ✓



&#x20; Caveat 1 (terminology): "Predictably-truncated" is a misnomer. $\\mathbf 1{\\cA\_t}$ is $\\sigma(u\_t,y\_t)$-measurable,

&#x20; i.e., $\\cH\_t$-measurable, not $\\cH\_{t-1}$-predictable. The mathematics of Freedman doesn't require predictable

&#x20; truncation (only the MDS property, which holds), so this is a naming inconsistency, not a bug.



&#x20; Caveat 2 (handwave): "$|\\Theta\_k|$ is polynomially small in $T$" is asserted without derivation. I verified:

&#x20; $\\E\[|u|^4\\mathbf 1{|u|^2>L^2}]$ via incomplete-Gamma decays like $(d\\log(4T/\\delta))^{d/2+1}(\\delta/(4T))^d /

&#x20; \\Gamma(d/2)$, giving $|\\Theta\_k| = O(\\text{polylog}\\cdot\\delta/T)$ for $d\\ge 1$. So the claim is true but the paper

&#x20; should either cite a lemma or add two lines. This handwave is a soft FLAG.



&#x20; ---

&#x20; (6) Corollary projector\_conf — VERIFIED



&#x20; Davis–Kahan for top-$r$ projectors with unperturbed gap $\\gamma=\\lambda\_{\\min}$ gives $|\\hat P - P|\\op \\le

&#x20; 2|E|\\op/\\gamma$ when $|E|<\\gamma/2$. Paper uses factor 4, which is conservative by $2\\times$ — valid. With $|E|\\le

&#x20; 2R\_X\\sqrt{\\log(2d/\\delta)/m\_k} + b\_\\sigma$ from Thm 5 (after dropping the $\\log/m\_k$ and $\\Theta\_k$ terms that are

&#x20; absorbed once $m\_k\\ge 4\\log(2d/\\delta)/9$ and $T$ large), Davis–Kahan yields $C\_{\\text{sub}}=8R\_X/\\lambda\_{\\min}$ and

&#x20; $\\Delta\_\\sigma = 4b\_\\sigma/\\lambda\_{\\min}$. ✓



&#x20; Minor: the corollary's intermediate bound $|\\widehat M\_k-\\bar M\_k^{\\text{probe}}|\\op \\le

&#x20; 2R\_X\\sqrt{\\log(2d/\\delta)/m\_k}+b\\sigma$ silently drops the $2R\_X\\log/(3m\_k)$ Bernstein term and $|\\Theta\_k|$. Both are

&#x20;  dominated for $m\_k$ large, but the statement should say "for $m\_k\\ge m\_0$ with $m\_0$ explicit" to be clean.



&#x20; ---

&#x20; (7) Proposition segment\_factorization — VERIFIED



&#x20; $\\theta\_t = B\_k^\\star w\_t$ on $\\cI\_k$ with $B\_k^\\star$ fixed ⇒ $\\theta\_t\\theta\_t^\\top = B\_k^\\star w\_tw\_t^\\top

&#x20; (B\_k^\\star)^\\top$. Taking conditional expectation and averaging over $\\cT\_k$ pulls $B\_k^\\star$ out linearly: $\\bar

&#x20; M\_k^{\\text{probe}} = B\_k^\\star \\bar S\_k^{\\text{probe}}(B\_k^\\star)^\\top$. Range equality: $\\bar S\_k^{\\text{probe}}\\succ

&#x20;  0$ with $\\lambda\_r\\ge\\lambda\_{\\min}$ (Lemma probe\_excitation\_conf), so it's invertible on $\\R^r$; $B\_k^\\star$ has

&#x20; orthonormal columns, so for $v \\ne 0 \\in \\text{range}(B\_k^\\star)$: write $v=B\_k^\\star a$, $a\\ne 0$; then $\\bar M\_k v =

&#x20;  B\_k^\\star \\bar S\_k a \\ne 0$, and $\\bar M\_k$ kills $\\text{range}(B\_k^\\star)^\\perp$. ⇒ $\\text{range}(\\bar M\_k) =

&#x20; \\text{range}(B\_k^\\star)$. ✓



&#x20; ---

&#x20; Summary



&#x20; ┌────────────────────────┬────────────────────────────────────────────────────────────────────────────────────────┐

&#x20; │         Claim          │                                         Status                                         │

&#x20; ├────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤

&#x20; │ (1) K\_inverse          │ VERIFIED                                                                               │

&#x20; ├────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤

&#x20; │ (2) quad\_conf          │ VERIFIED (restate $\\epsilon\_\\times$ and noise-variance assumptions conditionally)      │

&#x20; ├────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤

&#x20; │ (3) G\_unbiased         │ FLAGGED — derivation broken; true bias is exact scaled identity                        │

&#x20; │                        │ $-\\delta\_\\sigma/(d+2),I\_d$, stated upper bound holds only trivially                    │

&#x20; ├────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤

&#x20; │ (4) G\_bound            │ VERIFIED (constant slip at $d=1$, harmless)                                            │

&#x20; ├────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤

&#x20; │ (5)                    │ VERIFIED ("predictably truncated" is misnomer;                                         │

&#x20; │ matrix\_bernstein\_conf  │ $|\\Theta\_k|=O(\\text{polylog}\\cdot\\delta/T)$ should be stated)                          │

&#x20; ├────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤

&#x20; │ (6) projector\_conf     │ VERIFIED (factor 4 conservative; state $m\_k$ threshold)                                │

&#x20; ├────────────────────────┼────────────────────────────────────────────────────────────────────────────────────────┤

&#x20; │ (7)                    │ VERIFIED                                                                               │

&#x20; │ segment\_factorization  │                                                                                        │

&#x20; └────────────────────────┴────────────────────────────────────────────────────────────────────────────────────────┘



&#x20; One genuine FLAG (claim 3) plus several exposition fixes. The FLAG does not break downstream rates — they become

&#x20; pessimistic by a factor of $O(d^2\\log T)$ rather than wrong — but the proof as written is not a proof and must be

&#x20; rewritten to either (a) invoke vanishing third moments and derive $\\widetilde B\_t = -\\delta\_\\sigma/(d+2)I\_d$, or (b)

&#x20; explicitly do the truncated analysis with $\\mathbf 1{\\cA\_t}$ inside the expectation, which changes the lemma

&#x20; statement.









&#x20; ## Chunk A2 — GPT







\\textbf{(1) VERIFIED}



For each $(k,\\ell)$, $\\E\[(u^\\top M u)u\_k u\_\\ell]=\\sum\_{ij}M\_{ij}\\E\[u\_i u\_j u\_k u\_\\ell]=\\sum\_{ij}M\_{ij}(\\delta\_{ij}\\delta\_{k\\ell}+\\delta\_{ik}\\delta\_{j\\ell}+\\delta\_{i\\ell}\\delta\_{jk})=\\operatorname{tr}(M)\\delta\_{k\\ell}+M\_{k\\ell}+M\_{\\ell k}$, hence $K(M)=2M+\\operatorname{tr}(M)I\_d$.



If $X:=\\frac12N-\\frac{\\operatorname{tr}(N)}{2(d+2)}I\_d$, then $\\operatorname{tr}(X)=\\operatorname{tr}(N)/(d+2)$, so $K(X)=2X+\\operatorname{tr}(X)I\_d=N$.



The bound $\\|K^{-1}\\|\_{\\mathrm{op}}\\le 1$ is true but not tight: the exact norm is $d/(d+2)$, attained by $N=\\operatorname{diag}(1,-1,\\dots,-1)$.



\\bigskip



\\textbf{(2) FLAGGED}



The identity $\\E\[s\_t\\mid \\sigma(\\mathcal H\_{t-1},u\_t)]=u\_t^\\top \\widetilde M\_t u\_t+2u\_t^\\top m\_t-\\delta\_\\sigma$ is correct by expanding $y\_t^2=(u\_t^\\top\\theta\_t)^2+2\\varepsilon\_tu\_t^\\top\\theta\_t+\\varepsilon\_t^2$ and conditioning termwise.



The failure is the bound $\\|m\_t\\|\\le \\epsilon\_\\times$: the chunk’s setup only states $\\|\\E\[\\varepsilon\_t\\theta\_t]\\|\\le \\epsilon\_\\times$, which does \\emph{not} imply $\\|m\_t\\|=\\|\\E\[\\varepsilon\_t\\theta\_t\\mid \\mathcal H\_{t-1},u\_t]\\|\\le \\epsilon\_\\times$.



Concrete counterexample: $d=1$, $\\theta\_t\\equiv 1$, $\\varepsilon\_t=\\operatorname{sign}(u\_t)$; then $u\_t$ is independent of $(\\theta\_t,\\mathcal H\_{t-1})$, $\\E\[\\varepsilon\_t\\theta\_t]=0$, but $m\_t=\\operatorname{sign}(u\_t)$, so $|m\_t|=1\\not\\le 0$.



\\bigskip



\\textbf{(3a) VERIFIED}



Using linearity of $K^{-1}$, $\\E\[G\_t\\mid \\mathcal H\_{t-1}]=K^{-1}\\!\\big(\\E\[s\_tu\_tu\_t^\\top\\mid \\mathcal H\_{t-1}]\\big)$.



Substituting claim (2) gives

\\\[

K^{-1}( \\E\[(u\_t^\\top \\widetilde M\_t u\_t)u\_tu\_t^\\top\\mid \\mathcal H\_{t-1}] )

+K^{-1}( \\E\[2(u\_t^\\top m\_t)u\_tu\_t^\\top\\mid \\mathcal H\_{t-1}] )

\-\\delta\_\\sigma K^{-1}(\\E\[u\_tu\_t^\\top]).

\\]



Because $u\_t$ is independent of $(\\widetilde M\_t,\\mathcal H\_{t-1})$, the first term is $K^{-1}(K(\\widetilde M\_t))=\\widetilde M\_t$.



\\bigskip



\\textbf{(3b) FLAGGED}



The specific bad step is $\\| \\E\[(u\_t^\\top m\_t)u\_tu\_t^\\top]\\|\_{\\mathrm{op}}\\le L\\epsilon\_\\times\\cdot L^2$: no truncation has been imposed in Lemma $G\_{\\text{unbiased}}$, so replacing $\\|u\_t\\|$ by $L$ inside this unconditional expectation is invalid.



In the same counterexample as (2), $\\epsilon\_\\times=\\|\\E\[\\varepsilon\_t\\theta\_t]\\|=0$ but $m\_t=\\operatorname{sign}(u\_t)$, so $\\E\[(u\_t^\\top m\_t)u\_tu\_t^\\top]=\\E\[|u\_t|^3]=2\\sqrt{2/\\pi}\\neq 0$.



Hence the displayed bound $\\|\\E\[(u\_t^\\top m\_t)u\_tu\_t^\\top]\\|\_{\\mathrm{op}}\\le L^3\\epsilon\_\\times=0$ is false unless a \\emph{conditional} bound on $m\_t$ is added.



\\bigskip



\\textbf{(3c) VERIFIED}



Here $\\E\[u\_tu\_t^\\top]=I\_d$ exactly, because Lemma $G\_{\\text{unbiased}}$ is still working with the untruncated Gaussian probe law.



Applying claim (1) with $N=I\_d$ gives

\\\[

K^{-1}(I\_d)=\\frac12I\_d-\\frac{d}{2(d+2)}I\_d=\\frac{1}{d+2}I\_d,

\\]

so the bias term is exactly $-\\delta\_\\sigma (d+2)^{-1}I\_d$.



Therefore the “scaled identity” statement is exact; the parenthetical “after truncation, up to $1-O(\\delta/T)$” is misplaced in this lemma.



\\bigskip



\\textbf{(4a) FLAGGED}



Both indicators are indeed $\\sigma(u\_t,y\_t)$-measurable, so they are observable once round $t$ has been played.



But “predictable” means $\\mathcal H\_{t-1}$-measurable, and $\\mathbf 1\\{|y\_t|\\le L\_y\\}$ cannot be known at time $t-1$ because $y\_t$ is only revealed at round $t$.



So $\\mathcal A\_t$ is adapted/$\\mathcal H\_t$-measurable, \\emph{not} predictable; the proof can still use centering, but the word “predictable” is wrong.



\\bigskip



\\textbf{(4b) VERIFIED}



On $\\mathcal A\_t$, $|s\_t|=|y\_t^2-\\hat\\sigma^2|\\le y\_t^2+\\hat\\sigma^2\\le L\_y^2+\\hat\\sigma^2=:R\_s$.



Also

\\\[

\\|G\_t\\|\_{\\mathrm{op}}

=\\|K^{-1}(s\_tu\_tu\_t^\\top)\\|\_{\\mathrm{op}}

\\le \\|K^{-1}\\|\_{\\mathrm{op}}\\,|s\_t|\\,\\|u\_tu\_t^\\top\\|\_{\\mathrm{op}}

\\le R\_sL^2\\le R\_X.

\\]



The extra $+S\_w^2$ is unnecessary here because $G\_t$ is not centered in this lemma, but it makes the stated upper bound true.



\\bigskip



\\textbf{(4c) VERIFIED}



On $\\{\\|u\_t\\|\\le L\\}$, $|u\_t^\\top\\theta\_t|\\le \\|u\_t\\|\\,\\|\\theta\_t\\|\\le LS\_w$ because $\\|\\theta\_t\\|=\\|B\_k^\\star w\_t\\|\\le S\_w$.



Therefore $|y\_t|=|u\_t^\\top\\theta\_t+\\varepsilon\_t|\\le LS\_w+|\\varepsilon\_t|$.



So $\\{|y\_t|>L\_y\\}\\cap\\{\\|u\_t\\|\\le L\\}\\subseteq \\{|\\varepsilon\_t|>L\_\\varepsilon\\}$ with $L\_y=LS\_w+L\_\\varepsilon$.



\\bigskip



\\textbf{(4d) VERIFIED}



The noise part is clean: with $L\_\\varepsilon=\\sigma\_\\varepsilon\\sqrt{2\\log(4T/\\delta)}$, sub-Gaussianity gives

\\\[

\\Pr(|\\varepsilon\_t|>L\_\\varepsilon)\\le 2e^{-L\_\\varepsilon^2/(2\\sigma\_\\varepsilon^2)}=\\delta/(2T).

\\]



For the Gaussian probe, $\\|u\_t\\|^2\\sim\\chi\_d^2$, and Laurent--Massart gives an upper-tail bound that makes $\\Pr(\\|u\_t\\|>L)\\le \\delta/(4T)$ valid for $L^2=2d\\log(4T/\\delta)$; a Chernoff bound is actually the cleaner derivation here.



Hence

\\\[

\\Pr(\\mathcal A\_t^c)\\le \\delta/(4T)+\\delta/(2T)=3\\delta/(4T)\\le \\delta/T,

\\]

so the union bound gives $\\delta/T$, not $4\\delta/T$.



\\bigskip



\\textbf{(5a) VERIFIED}



$\\tilde G\_t=G\_t\\mathbf 1\\{\\mathcal A\_t\\}$ is $\\mathcal H\_t$-measurable because $G\_t$ and $\\mathbf 1\\{\\mathcal A\_t\\}$ are both functions of round-$t$ observables.



By definition,

\\\[

\\tilde X\_t=\\tilde G\_t-\\E\[\\tilde G\_t\\mid \\mathcal H\_{t-1}].

\\]



Therefore $\\E\[\\tilde X\_t\\mid \\mathcal H\_{t-1}]=0$ identically; this part is just centering.



\\bigskip



\\textbf{(5b) VERIFIED}



On $\\mathcal A\_t$, claim (4b) gives $\\|\\tilde G\_t\\|\_{\\mathrm{op}}=\\|G\_t\\|\_{\\mathrm{op}}\\le R\_X$, and on $\\mathcal A\_t^c$ one has $\\tilde G\_t=0$.



So $\\|\\tilde G\_t\\|\_{\\mathrm{op}}\\le R\_X$ almost surely without any conditioning.



Then

\\\[

\\|\\tilde X\_t\\|\_{\\mathrm{op}}

\\le \\|\\tilde G\_t\\|\_{\\mathrm{op}}+\\|\\E\[\\tilde G\_t\\mid\\mathcal H\_{t-1}]\\|\_{\\mathrm{op}}

\\le 2R\_X.

\\]



\\bigskip



\\textbf{(5c) VERIFIED}



Let $\\mu\_t:=\\E\[\\tilde G\_t\\mid\\mathcal H\_{t-1}]$; then

\\\[

\\E\[\\tilde X\_t^2\\mid\\mathcal H\_{t-1}]

=\\E\[(\\tilde G\_t-\\mu\_t)^2\\mid\\mathcal H\_{t-1}]

=\\E\[\\tilde G\_t^2\\mid\\mathcal H\_{t-1}]-\\mu\_t^2

\\preceq \\E\[\\tilde G\_t^2\\mid\\mathcal H\_{t-1}].

\\]



Since $\\tilde G\_t$ is self-adjoint and $\\|\\tilde G\_t\\|\_{\\mathrm{op}}\\le R\_X$, we have $\\tilde G\_t^2\\preceq R\_X^2I$ almost surely.



Thus

\\\[

\\E\[\\tilde X\_t^2\\mid\\mathcal H\_{t-1}]\\preceq R\_X^2I.

\\]



\\bigskip



\\textbf{(5d) VERIFIED}



Tropp’s matrix Freedman theorem states that for self-adjoint martingale differences with $\\lambda\_{\\max}(X\_t)\\le R$ and predictable quadratic variation bounded by $\\sigma^2$, one has a Bernstein/Freedman tail of the form

\\\[

\\exp\\!\\left(-\\frac{t^2}{2(\\sigma^2+Rt/3)}\\right).

\\]



Here $R=2R\_X$ and $\\sigma^2\\le m\_kR\_X^2$, so after the two-sided $2d$ union bound one gets

\\\[

\\left\\|\\frac1{m\_k}\\sum\_t \\tilde X\_t\\right\\|\_{\\mathrm{op}}

\\lesssim \\sqrt{2}\\,R\_X\\sqrt{\\log(2d/\\delta)/m\_k}

+\\frac{2R\_X\\log(2d/\\delta)}{3m\_k}.

\\]



Therefore the paper’s coefficient $2R\_X$ in front of the square-root term is a valid but looser simplification of the Freedman form.



\\bigskip



\\textbf{(5e) VERIFIED}



Write

\\\[

\\bar{\\tilde G}\_k:=m\_k^{-1}\\sum\_{t\\in\\mathcal T\_k}\\tilde G\_t

\\qquad\\text{and}\\qquad

\\bar\\mu\_k:=m\_k^{-1}\\sum\_{t\\in\\mathcal T\_k}\\E\[\\tilde G\_t\\mid\\mathcal H\_{t-1}];

\\]

then

\\\[

m\_k^{-1}\\sum\_t\\tilde X\_t=\\bar{\\tilde G}\_k-\\bar\\mu\_k.

\\]



On $\\mathcal E=\\bigcap\_t\\mathcal A\_t$, $\\tilde G\_t=G\_t$, so $\\bar{\\tilde G}\_k=\\widehat M\_k$, while

\\\[

\\bar\\mu\_k

=

m\_k^{-1}\\sum\_t\\bigl(\\E\[G\_t\\mid\\mathcal H\_{t-1}]-\\E\[G\_t\\mathbf 1\\{\\mathcal A\_t^c\\}\\mid\\mathcal H\_{t-1}]\\bigr)

=

\\bar M\_k^{\\mathrm{probe}}+\\widetilde B-\\Theta\_k.

\\]



Hence

\\\[

\\widehat M\_k-\\bar M\_k^{\\mathrm{probe}}-\\widetilde B

=

\\left(m\_k^{-1}\\sum\_t\\tilde X\_t\\right)-\\Theta\_k

\\]

on $\\mathcal E$; the identity is correct, although $\\Theta\_k$ is predictable/random, not deterministic.



\\bigskip



\\textbf{(5f) VERIFIED}



Lemma $G\_{\\text{bound}}$ gives $\\Pr(\\mathcal E^c)\\le \\delta$.



Tropp-Freedman gives another failure event of size at most $\\delta$.



So the intersection event has probability at least $1-2\\delta$; the bookkeeping itself is correct.



\\bigskip



\\textbf{(6a) VERIFIED}



From Proposition segment\\\_factorization,

\\\[

\\bar M\_k^{\\mathrm{probe}}=B\_k^\\star \\bar S\_k^{\\mathrm{probe}}(B\_k^\\star)^\\top.

\\]



If $\\lambda\_r(\\bar S\_k^{\\mathrm{probe}})\\ge \\lambda\_{\\min}>0$, then $\\bar S\_k^{\\mathrm{probe}}$ is full rank $r$, so $\\bar M\_k^{\\mathrm{probe}}$ has exactly $r$ positive eigenvalues.



Those nonzero eigenvalues equal the eigenvalues of $\\bar S\_k^{\\mathrm{probe}}$, so the $r$-th eigenvalue is at least $\\lambda\_{\\min}$.



\\bigskip



\\textbf{(6b) VERIFIED}



Because $\\bar M\_k^{\\mathrm{probe}}$ is PSD of rank $r$, its eigengap at the signal/noise split is

\\\[

\\lambda\_r(\\bar M\_k^{\\mathrm{probe}})-\\lambda\_{r+1}(\\bar M\_k^{\\mathrm{probe}})\\ge \\lambda\_{\\min}.

\\]



A Davis--Kahan/Yu--Wang--Samworth population-gap bound gives

\\\[

\\|\\sin\\Theta(\\widehat U\_k,U\_k^\\star)\\|\_{\\mathrm{op}}

\\le 2\\|\\widehat M\_k-\\bar M\_k^{\\mathrm{probe}}\\|\_{\\mathrm{op}}/\\lambda\_{\\min},

\\]

and for equal-rank subspaces

\\\[

\\|\\widehat P\_k-P\_k^\\star\\|\_{\\mathrm{op}}=\\|\\sin\\Theta\\|\_{\\mathrm{op}}.

\\]



So the constant $4$ is conservative but correct; the cleaner operator-norm constant here is $2$, not $4$.



\\bigskip



\\textbf{(6c) FLAGGED}



The corollary proof drops two positive terms that are present in Theorem $\\text{matrix\\\_bernstein\\\_conf}$: the linear Freedman term $\\frac{2R\_X\\log(2d/\\delta)}{3m\_k}$ and the truncation-bias term $\\|\\Theta\_k\\|\_{\\mathrm{op}}$.



Concrete counterexample to the derivation: if $m\_k=1$ and $\\log(2d/\\delta)=16$, then after the paper’s own factor $4/\\lambda\_{\\min}$ the omitted linear term alone contributes

\\\[

128R\_X/(3\\lambda\_{\\min}),

\\]

which is not absorbed by

\\\[

C\_{\\mathrm{sub}}\\sqrt{\\log(2d/\\delta)/m\_k}=32R\_X/\\lambda\_{\\min}.

\\]



So the displayed final bound needs extra assumptions explicitly controlling both dropped terms; as written, it does not follow from the preceding theorem.



\\bigskip



\\textbf{(7) VERIFIED}



For every probe time $t\\in\\mathcal T\_k$,

\\\[

\\widetilde M\_t=\\E\[\\theta\_t\\theta\_t^\\top\\mid\\mathcal H\_{t-1}]

=

B\_k^\\star \\E\[w\_tw\_t^\\top\\mid\\mathcal H\_{t-1}] (B\_k^\\star)^\\top.

\\]



Averaging over $t\\in\\mathcal T\_k$ gives

\\\[

\\bar M\_k^{\\mathrm{probe}}=B\_k^\\star \\bar S\_k^{\\mathrm{probe}} (B\_k^\\star)^\\top.

\\]



If $\\lambda\_r(\\bar S\_k^{\\mathrm{probe}})\\ge \\lambda\_{\\min}>0$, then $\\bar S\_k^{\\mathrm{probe}}$ is invertible on $\\mathbb R^r$, so

\\\[

\\operatorname{range}(\\bar M\_k^{\\mathrm{probe}})=\\operatorname{range}(B\_k^\\star).

\\]



\\bigskip



Bottom line: the hard breaks are \\textbf{(2)}, \\textbf{(3b)}, \\textbf{(4a)}, and \\textbf{(6c)}. The most serious structural issue is that the proof quietly upgrades an \\emph{unconditional} coupling bound into a \\emph{conditional} one, and that invalidates the bias control in $G\_{\\text{unbiased}}$; the “predictable truncation” wording is also false, though the MDS centering step itself survives.





\-----



&#x20; ## Chunk A3 — minimax LB



\### Claude response



\\section\*{Adversarial audit of \\texttt{chunk\_A3\_minimax\_lb.tex}}



&#x20; \\subsection\*{(1) Local packing with matched upper/lower op-norm diameters}



&#x20; \\textbf{FLAGGED.} The equation

&#x20; \[

&#x20; \\tfrac12\\Delta ;\\le; |P\_{V\_i}-P\_{V\_j}|{\\mathrm{op}} ;\\le; 2\\Delta,\\qquad \\log N\\ge c\_0,r(d-r),

&#x20; ]

&#x20; is a true existence statement (via a volumetric packing of an op-norm ball of radius $2\\Delta$ in a tangent chart of

&#x20; $\\mathrm{Gr}(r,d)$, using

&#x20; $\\log!\\bigl\[\\mathrm{vol}(B{\\mathrm{op}}(2\\Delta))/\\mathrm{vol}(B\_{\\mathrm{op}}(\\Delta/2))\\bigr]\\ge r(d-r)\\log 4$), but

&#x20;  the cited reference \\emph{does not supply it}.



&#x20; Cai--Ma--Wu (2013), Lem.\~1, gives a packing

&#x20; \[

&#x20; |P\_{V\_i}-P\_{V\_j}|\_F;\\ge;c',\\epsilon\\sqrt{r},\\qquad \\log N;\\gtrsim;r(d-r),

&#x20; ]

&#x20; i.e.\\ only a \\emph{Frobenius-norm lower} bound. Wainwright 2019 Ch.\~15 (Example 15.14) likewise develops the

&#x20; construction via Varshamov--Gilbert on $\\pm 1$ blocks, whose pairwise contrast is controlled in F-norm, not op-norm.



&#x20; Translating the F-norm separation to op-norm loses a factor $\\sqrt{2r}$: if $|G\_i-G\_j|F\\asymp\\epsilon\\sqrt{r(d-r)}$

&#x20; then

&#x20; \[

&#x20; |\\Pi{ij}|{\\mathrm{op}};\\ge;|\\Pi{ij}|F/\\sqrt{2r};\\gtrsim;\\epsilon\\sqrt{(d-r)/r},\\qquad

&#x20; |\\Pi{ij}|{\\mathrm{op}};\\le;|\\Pi{ij}|\_F;\\lesssim;\\epsilon\\sqrt{r(d-r)},

&#x20; ]

&#x20; a gap of $\\sqrt{2r}$, not the factor $4$ claimed. So the \\emph{specific} citation does not deliver the stated

&#x20; two-sided op-norm packing. The cleanest fix is to cite Szarek's Grassmannian metric-entropy bound (or do the local

&#x20; volumetric construction explicitly); the claim itself survives.



&#x20; \\subsection\*{(2) Isserlis identity and $\\mathrm{tr},\\Pi\_{ij}=0$}



&#x20; \\textbf{VERIFIED.} For $u\\sim\\mathcal N(0,I\_d)$ and symmetric $M$,

&#x20; \[

&#x20; \\mathbb E\[(u^\\top Mu)^2]=\\sum\_{ijkl}M\_{ij}M\_{kl},\\mathbb E\[u\_iu\_ju\_ku\_l]

&#x20; =\\sum\_{ijkl}M\_{ij}M\_{kl}(\\delta\_{ij}\\delta\_{kl}+\\delta\_{ik}\\delta\_{jl}+\\delta\_{il}\\delta\_{jk}),

&#x20; ]

&#x20; and the three sums evaluate to $(\\mathrm{tr},M)^2$, $|M|F^2$, $\\mathrm{tr}(M^2)=|M|F^2$ respectively (last two equal

&#x20; by symmetry). Total: $(\\mathrm{tr},M)^2+2|M|F^2$. For $\\Pi{ij}=P{V\_i}-P{V\_j}$, both projectors have trace $r$, so

&#x20; $\\mathrm{tr},\\Pi\_{ij}=0$. Caveat: probes are truncated at $|u|\\le L$, so the exact identity requires absorbing a

&#x20; $(1+o(1))$ factor into $C\_1$; this is standard.



&#x20; \\subsection\*{(3) Frobenius bound via rank}



&#x20; \\textbf{VERIFIED.} $\\mathrm{rank}(\\Pi\_{ij})\\le\\mathrm{rank}(P\_{V\_i})+\\mathrm{rank}(P\_{V\_j})\\le 2r$. For any matrix $M$

&#x20;  of rank $k$, $|M|F^2=\\sum{i=1}^k\\sigma\_i(M)^2\\le k,\\sigma\_1(M)^2=k,|M|{\\mathrm{op}}^2$. Hence $|\\Pi{ij}|F^2\\le

&#x20; 2r|\\Pi{ij}|\_{\\mathrm{op}}^2\\le 2r(2\\Delta)^2=8r\\Delta^2$.



&#x20; \\subsection\*{(4) KL tensorization and identical probe marginal}



&#x20; \\textbf{VERIFIED.} Setup fixes probes $u\_t\\sim\\mathcal N(0,I\_d)$ truncated at $L$, independent of $B^\\star$; the

&#x20; $\\mathcal H\_m$-measurable estimator is over the \\emph{estimator} class, not an adaptive probing strategy, so the probe

&#x20;  law is instance-independent. Then

&#x20; \[

&#x20; \\mathrm{KL}(\\nu\_i(u,y),|,\\nu\_j(u,y))=\\mathrm{KL}(\\nu\_i(u),|,\\nu\_j(u))+\\mathbb E\_u\[\\mathrm{KL}(\\nu\_i(y\\mid

&#x20; u),|,\\nu\_j(y\\mid u))]=0+\\mathbb E\_u\[\\mathrm{KL}(\\cdot\\mid u)],

&#x20; ]

&#x20; and iid rounds give $\\mathrm{KL}(\\nu\_i^{\\otimes m}|\\nu\_j^{\\otimes m})=m\\cdot\\mathrm{KL}(\\nu\_i|\\nu\_j)$.



&#x20; \\subsection\*{(5) Fano constant $\\tfrac14\\log N$}



&#x20; \\textbf{FLAGGED (minor).} Tsybakov 2009, Thm.\~2.5 actually states: if

&#x20; $\\tfrac{1}{M+1}\\sum\_j\\mathrm{KL}(P\_j|P\_0)\\le\\alpha\\log M$ with $\\alpha<1/8$, then

&#x20; \[

&#x20; \\inf\_{\\hat\\theta}\\max\_j P\_j(\\hat\\theta\\ne\\theta\_j);\\ge;\\frac{\\sqrt M}{1+\\sqrt

&#x20; M}\\Bigl(1-2\\alpha-\\sqrt{\\tfrac{2\\alpha}{\\log M}}\\Bigr),

&#x20; ]

&#x20; \\emph{not} the quoted $K\\le\\tfrac14\\log N\\Rightarrow P\_e\\ge1/2$''. The quoted form is the textbook Fano'' derived from

&#x20;  $P\_e\\ge 1-(K+\\log 2)/\\log N$: requiring $P\_e\\ge1/2$ gives $K\\le(\\log N)/2-\\log 2$, which is implied by

&#x20; $K\\le\\tfrac14\\log N$ only when $\\log N\\ge 4\\log 2$, i.e.\\ $N\\ge 16$. This side-condition is not stated but is

&#x20; automatic since $\\log N\\ge c\_0 r(d-r)$. Re-citing Tsybakov 2009, Prop.\~2.3 (Fano's lemma)'' or Cor.\~2.6'' would be

&#x20; accurate; Thm.\~2.5 gives a sharper but different statement.



&#x20; \\subsection\*{(6) Final balance and $r$-cancellation}



&#x20; \\textbf{VERIFIED.} Impose $C\_1mr\\Delta^2\\le\\tfrac14\\log N$; use $\\log N\\ge c\_0 r(d-r)$ to reduce to the sufficient

&#x20; condition $\\Delta^2\\le c\_0(d-r)/(4C\_1m)$ (the factor $r$ cancels). Saturating:

&#x20; \[

&#x20; \\Delta=\\tfrac12\\sqrt{c\_0(d-r)/(C\_1m)},\\qquad \\Delta/8=\\tfrac{1}{16}\\sqrt{c\_0(d-r)/(C\_1m)}=c\_1/\\sqrt m,

&#x20; ]

&#x20; with $c\_1=\\tfrac{1}{16}\\sqrt{c\_0(d-r)/C\_1}=\\Theta(\\sqrt{d-r})$, valid for $m\\ge c\_0(d-r)/C\_1$ (the regime where

&#x20; $\\Delta\\le1/2$).



&#x20; \\subsection\*{(7) Identifiability corollary ``$m\\ge c(d-r)$ for constant risk''}



&#x20; \\textbf{FLAGGED.} The \\emph{rate} claim $m=\\Omega(d-r)$ is consistent with $c\_1=\\Theta(\\sqrt{d-r})$, but the

&#x20; \\emph{specific constant} $1/4$ is unreachable by the theorem as proved. With

&#x20; \[

&#x20; c\_1=\\tfrac{1}{16}\\sqrt{c\_0(d-r)/C\_1},\\qquad 16c\_1^2=\\tfrac{c\_0(d-r)}{16C\_1},

&#x20; ]

&#x20; the window ``$c\_1/\\sqrt m\\ge 1/4$'' demands $m\\le 16c\_1^2=c\_0(d-r)/(16C\_1)$, which lies \\emph{below} the regime of

&#x20; validity $m\\ge c\_0(d-r)/C\_1$. The two ranges are disjoint, so in the regime where the bound $c\_1/\\sqrt m$ is proved,

&#x20; one always has

&#x20; \[

&#x20; c\_1/\\sqrt m;\\le;c\_1/\\sqrt{c\_0(d-r)/C\_1};=;1/16;<;1/4.

&#x20; ]

&#x20; The full piecewise lower bound (including the $\\Delta=1/2$ cap for small $m$) is

&#x20; $\\Delta/8=\\tfrac{1}{16}\\min(1,\\sqrt{c\_0(d-r)/(C\_1m)})\\le 1/16$, never $\\ge 1/4$.



&#x20; \\textbf{Counterexample to the corollary's proof as written:} take any $m\\ge 1$; the theorem does not exclude an

&#x20; estimator with risk $\\in(1/16,1/4)$, so ``risk $<1/4$'' says nothing about $m$ via Theorem\~\\ref{thm:minimax\_recovery}.

&#x20;  Concrete fix: either (a) state the corollary at target $1/32$ (or any $\\epsilon<1/16$), giving $m\\ge

&#x20; c\_1^2/\\epsilon^2=\\Theta(d-r)$ consistently; or (b) strengthen the theorem with a \\emph{global} (non-local) packing

&#x20; argument to reach $\\Omega(1)$ lower bounds for constant target risk.



&#x20; \\subsection\*{Summary}



&#x20; \\begin{center}

&#x20; \\begin{tabular}{cl}

&#x20; (1) \& FLAGGED — citation/construction mismatch (F-norm vs op-norm); claim itself recoverable via Szarek.\\

&#x20; (2) \& VERIFIED (modulo truncation constant).\\

&#x20; (3) \& VERIFIED.\\

&#x20; (4) \& VERIFIED.\\

&#x20; (5) \& FLAGGED (minor) — wrong Tsybakov number; inequality holds for $N\\ge 16$.\\

&#x20; (6) \& VERIFIED.\\

&#x20; (7) \& FLAGGED — constant $1/4$ exceeds achievable lower-bound value $1/16$; restate at $\\epsilon<1/16$.

&#x20; \\end{tabular}

&#x20; \\end{center}



&#x20; \\textbf{Net verdict:} the rate $c\_1/\\sqrt m$ with $c\_1=\\Theta(\\sqrt{d-r})$ is correct. The two substantive gaps are

&#x20; the Grassmannian-packing citation (1) and the constant in the identifiability corollary (7); both are fixable without

&#x20; changing the rate.





&#x20;### GPT response



\\paragraph\*{Claim (1)} \\textbf{FLAGGED.}\\

The exact source I could locate is: Cai--Ma--Wu Lemma 1 gives a \\emph{local packing number inside a ball}, but for the Frobenius metric (\\rho(P,Q)=|P-Q|\*F); Pajor's Proposition 8 is the operator-norm ((\\sigma\*\\infty)) entropy statement. (\[arXiv]\[1])\\

So the cited reference does \\emph{not} directly imply (\\frac{\\Delta}{2}\\le |P\_{V\_i}-P\_{V\_j}|\_{\\op}\\le 2\\Delta) at the same scale; there is a metric mismatch between (|\\cdot|\*F) and (|\\cdot|\*{\\op}).\\

Concrete counterexample to that substitution: if all (r) principal angles between (V,W) equal (\\theta) with (\\sin\\theta=\\Delta/\\sqrt{2r}), then (|P\_V-P\_W|\*F=\\Delta) but (|P\_V-P\_W|\*{\\op}=\\Delta/\\sqrt{2r}<\\Delta/2) for (r\\ge 3).



\\paragraph\*{Claim (2)} \\textbf{FLAGGED.}\\

The identity itself is correct: (\\mathbb E\[(u^\\top M u)^2]=\\sum\_{ijkl}M\_{ij}M\_{kl}(\\delta\_{ij}\\delta\_{kl}+\\delta\_{ik}\\delta\_{jl}+\\delta\_{il}\\delta\_{jk})=(\\operatorname{tr}M)^2+2|M|\*F^2) for symmetric (M), and (\\operatorname{tr}\\Pi\*{ij}=\\operatorname{tr}P\_{V\_i}-\\operatorname{tr}P\_{V\_j}=r-r=0).\\

The failing step is the \\emph{application}: the instances were defined with probes truncated to ({|u|\\le L}), but the proof then marginalizes as if (u\\sim\\mathcal N(0,I\_d)) unconditionally.\\

Concrete counterexample: for (d=1), (M=\[1]), (L=1), one has (\\mathbb E\[u^4\\mid |u|\\le1]\\neq 3=\\mathbb E\_{Z\\sim\\mathcal N(0,1)}\[Z^4]); the untruncated Isserlis formula is not the law actually used in the model.



\\paragraph\*{Claim (3)} \\textbf{VERIFIED.}\\

(\\operatorname{rank}(P-Q)\\le \\operatorname{rank}(P)+\\operatorname{rank}(Q)=2r), so (|P-Q|\*F^2\\le \\operatorname{rank}(P-Q)|P-Q|\*{\\op}^2\\le 2r|P-Q|\_{\\op}^2).\\

This is just (\\sum\_k s\_k(A)^2\\le (\\max\_k s\_k(A)^2)\\cdot #{k:s\_k(A)\\neq0}) applied to (A=P-Q).\\

The constant (2) is tight: with (P=\\operatorname{diag}(I\_r,0\_r,0)) and (Q=\\operatorname{diag}(0\_r,I\_r,0)), one gets (|P-Q|\*F^2=2r) and (|P-Q|\*{\\op}=1).



\\paragraph\*{Claim (4)} \\textbf{VERIFIED.}\\

For one round, both models have the same probe marginal (Q\_L) (the common truncated-Gaussian law), and only the conditional law of (y) given (u) changes.\\

Hence by the KL chain rule, (\\mathrm{KL}(P\_i^{u,y}|P\_j^{u,y})=\\mathrm{KL}(Q\_L|Q\_L)+\\mathbb E\_{u\\sim Q\_L}!\\left\[\\mathrm{KL}(P\_i^{y|u}|P\_j^{y|u})\\right]=\\mathbb E\_{u\\sim Q\_L}\[\\mathrm{KL}(\\cdot)]).\\

Independence across (m) rounds then gives (\\mathrm{KL}(\\nu\_i^{\\otimes m}|\\nu\_j^{\\otimes m})=m,\\mathbb E\_{u\\sim Q\_L}!\\left\[\\mathrm{KL}(\\nu\_i^{y|u}|\\nu\_j^{y|u})\\right]).



\\paragraph\*{Claim (5)} \\textbf{FLAGGED.}\\

Tsybakov Theorem (2.5) is the many-hypothesis \\emph{Kullback version}: if (\\frac1M\\sum\_{j=1}^M K(P\_j,P\_0)\\le \\alpha\\log M) with (0<\\alpha<1/8), then the testing error is bounded below by (\\frac{\\sqrt M}{1+\\sqrt M}\\bigl(1-2\\alpha-\\sqrt{2\\alpha/\\log M}\\bigr)); Theorem (2.7) is only the general-loss wrapper. (\[University of Southampton]\[2])\\

So ``(\\max \\mathrm{KL}\\le \\frac14\\log N \\Rightarrow P\_{\\mathrm{err}}\\ge \\frac12)'' is \\emph{not} the stated Tsybakov theorem, and the constant (\\frac14) does not match Theorem (2.5).\\

Concrete counterexample to the claimed implication: for (N=2), (P\_0=\\mathrm{Bern}(0.5)), (P\_1=\\mathrm{Bern}(0.7)), one has (\\max{K(P\_0,P\_1),K(P\_1,P\_0)}<\\frac14\\log 2), but the optimal one-sample testing error is (0.4<1/2).



\\paragraph\*{Claim (6)} \\textbf{VERIFIED.}\\

The algebra is correct: (C\_1mr\\Delta^2\\le \\frac14 c\_0 r(d-r)) implies (\\Delta^2\\le \\frac{c\_0(d-r)}{4C\_1m}) because the factor (r) cancels exactly.\\

Then (\\Delta/8\\ge c\_1/\\sqrt m) with (c\_1=\\frac1{16}\\sqrt{c\_0(d-r)/C\_1}), so indeed (c\_1=\\Theta(\\sqrt{d-r})).\\

This is only the balancing step; it is conditional on the earlier packing, KL, and Fano steps being valid.



\\paragraph\*{Claim (7)} \\textbf{VERIFIED.}\\

Yes: if (\\inf\_{\\widehat P}\\sup\_\\nu \\mathbb E\_\\nu|\\widehat P-P^\\star|\*{\\op}\\ge c\_1/\\sqrt m) and (c\_1=\\Theta(\\sqrt{d-r})), then forcing the risk below (1/4) requires (c\_1/\\sqrt m<1/4).\\

Equivalently, any estimator with constant risk (\\le 1/4) must satisfy (m>16c\_1^2=\\Theta(d-r)).\\

So the identifiability threshold (m\\ge c\*{\\mathrm{id}}(d-r)) is consistent; the proof just needs the contraposition written with the inequality in the correct direction.



\[1]: https://arxiv.org/pdf/1211.1309 "https://arxiv.org/pdf/1211.1309"

\[2]: https://www.personal.soton.ac.uk/cz1y20/Reading\_Group/mlts-2023w/Tsybakov\_Nonparametric\_Estimation.pdf "https://www.personal.soton.ac.uk/cz1y20/Reading\_Group/mlts-2023w/Tsybakov\_Nonparametric\_Estimation.pdf"



\---------



&#x20;## Chunk A4 — main upper bound



&#x20; ### Claude response



\\textbf{Claim (1): Optimism Decomposition --- FLAGGED (sign slip; conclusion survives via $|\\cdot|$).}



&#x20; \\textbf{Re-derivation from scratch.} Let $\\mathrm{UCB}(x) := (\\widehat U\_{t-1}^\\top x)^\\top \\widehat a\_t +

&#x20; \\beta\_t^{(r,W)}|\\widehat U\_{t-1}^\\top x|{\\widetilde V\_t^{-1}} + \\gamma\_t|x|$. Optimism gives $x\_t^{\\star\\top}\\theta\_t

&#x20; \\le \\mathrm{UCB}(x\_t^\\star) \\le \\mathrm{UCB}(x\_t)$ (the second by argmax selection). Therefore

&#x20; \[

&#x20; \\Delta\_t ;\\le; \\mathrm{UCB}(x\_t) - x\_t^\\top\\theta\_t ;=; x\_t^\\top\\bigl(\\widehat U{t-1}\\widehat a\_t - \\theta\_t\\bigr) +

&#x20; \\beta\_t^{(r,W)}|\\widehat U\_{t-1}^\\top x\_t|{\\widetilde V\_t^{-1}} + \\gamma\_t|x\_t|.

&#x20; ]

&#x20; Now using $\\widehat P{t-1}\\theta\_t = \\widehat U\_{t-1}a\_t^\\star$,

&#x20; \[

&#x20; x\_t^\\top(\\widehat U\_{t-1}\\widehat a\_t - \\theta\_t)

&#x20; = x\_t^\\top \\widehat U\_{t-1}(\\widehat a\_t - a\_t^\\star) ;-; x\_t^\\top(I-\\widehat P\_{t-1})\\theta\_t.

&#x20; ]

&#x20; \\textbf{Issue.} The chunk's display (lines 68--75) writes $x\_t^\\top(\\theta\_t - \\widehat U\_{t-1}\\widehat a\_t)$ and

&#x20; $+x\_t^\\top(I-\\widehat P\_{t-1})\\theta\_t$, i.e.\\ the \\emph{opposite} sign of what optimism actually yields. The error is

&#x20;  harmless because (i.a) immediately replaces the first piece by $|x\_t^\\top(I-\\widehat P\_{t-1})\\theta\_t|$ and (i.b)

&#x20; replaces the second by $|(\\widehat a\_t - a\_t^\\star)^\\top z\_t|$, so both are absolute-valued. \\textbf{The bound on

&#x20; $\\Delta\_t$ as stated holds with absolute values}, but the intermediate equality is sign-wrong as written --- a referee

&#x20;  will mark this. Also: $\\gamma\_t$ is undefined in the setup; it must satisfy $\\gamma\_t \\ge S\_w\\varepsilon\_k$ for

&#x20; optimism to actually hold (to absorb $|x^\\top(I-\\widehat P)\\theta|/|x| \\le S\_w\\varepsilon\_k$), and at this magnitude

&#x20; $\\sum\_t\\gamma\_t|x\_t| \\le \\sum\_k R\_\\cA S\_w\\varepsilon\_k n\_k$, identical in order to the (i.a) term --- consistent with

&#x20; (i.c) silently dropping it.



&#x20; \\textbf{Verdict:} Result correct as bound; intermediate sign and undefined $\\gamma\_t$ should be fixed for

&#x20; camera-ready.



&#x20; \\medskip



&#x20; \\textbf{Claim (2): Equal-rank projector identity --- VERIFIED.}



&#x20; Both $P^\\star, \\widehat P$ are orthogonal projectors of equal rank $r$; $B^\\star$ has orthonormal columns spanning

&#x20; $\\mathrm{range}(P^\\star)$, so $P^\\star B^\\star = B^\\star$. Thus

&#x20; \[

&#x20; (I-\\widehat P)B^\\star ;=; (I-\\widehat P)P^\\star B^\\star ;=; (I-\\widehat P)(P^\\star - \\widehat P)B^\\star +

&#x20; \\underbrace{(I-\\widehat P)\\widehat P}{=,0}, B^\\star ;=; (I-\\widehat P)(P^\\star-\\widehat P)B^\\star.

&#x20; ]

&#x20; Submultiplicativity with $|I-\\widehat P|\\op = 1$ and $|B^\\star|\\op = 1$ gives $|(I-\\widehat P)B^\\star|\\op \\le |P^\\star

&#x20;  - \\widehat P|\_\\op = \\varepsilon\_k$. $\\square$



&#x20; \\medskip



&#x20; \\textbf{Claim (3): Application $\\bar\\xi\_k = R\_\\cA S\_w \\varepsilon\_k$ --- VERIFIED (with one tacit assumption).}



&#x20; $|\\xi\_s| = |x\_s^\\top(I-\\widehat P\_{s-1})\\theta\_s| \\le |x\_s|\\cdot|(I-\\widehat P\_{s-1})\\theta\_s| \\le R\_\\cA,|(I-\\widehat

&#x20; P\_{s-1})B\_k^\\star w\_s| \\le R\_\\cA,|(I-\\widehat P\_{s-1})B\_k^\\star|\\op,|w\_s| \\le R\\cA,\\varepsilon\_k,S\_w$, where the last

&#x20; uses claim (2) (with $P^\\star \\leftarrow P\_k^\\star = B\_k^\\star B\_k^{\\star\\top}$) and $|w\_s| \\le S\_w$.



&#x20; \\textbf{Tacit assumption flagged:} the inequality $|(I-\\widehat P\_{s-1})B\_k^\\star|\\op \\le \\varepsilon\_k$ requires

&#x20; $\\widehat P{s-1} = \\widehat P\_k$ for all $s$ in the exploitation phase of segment $k$ (otherwise $\\widehat P\_{s-1}$

&#x20; could differ from the segment-$k$ projector that defines $\\varepsilon\_k$). The setup at lines 18--21 is consistent

&#x20; with this --- $\\widehat U$ is updated only after each segment's probe phase --- but the chunk should make this

&#x20; explicit.



&#x20; I'll continue with claims (4)--(7) next.





&#x20; ### GPT response





\\textbf{Audit of the uploaded proof.} ; 



\\textbf{(1) FLAGGED.}\\

From optimism, (x\_t^{\\star\\top}\\theta\_t \\le x\_t^\\top \\widehat U\_{t-1}\\widehat a\_t + \\beta\_t^{(r,W)}|\\widehat U\_{t-1}^\\top x\_t|\*{\\widetilde V\_t^{-1}} + \\gamma\_t|x\_t|), hence

\[

\\Delta\_t \\le x\_t^\\top(\\widehat U\*{t-1}\\widehat a\_t-\\theta\_t)+\\beta\_t^{(r,W)}|\\widehat U\_{t-1}^\\top x\_t|\*{\\widetilde V\_t^{-1}}+\\gamma\_t|x\_t|,

]

not the sign written in lines (68\\text{--}70).\\

Concrete counterexample: (d=r=1), (\\theta\_t=1), (\\widehat U\*{t-1}=1), (\\widehat a\_t=2), (\\beta\_t^{(r,W)}=\\gamma\_t=0), (\\mathcal A\_t={0,1}); then (x\_t=x\_t^\\star=1), so (\\Delta\_t=0), but the proof’s RHS equals (-1).



\\textbf{(2) VERIFIED.}\\

Since (P^\\star=B^\\star B^{\\star\\top}) projects onto (\\operatorname{col}(B^\\star)), one has (P^\\star B^\\star=B^\\star).\\

Also ((I-\\widehat P)\\widehat P=0), so

\[

(I-\\widehat P)B^\\star=(I-\\widehat P)P^\\star B^\\star=(I-\\widehat P)(P^\\star-\\widehat P)B^\\star .

]

Therefore

\[

|(I-\\widehat P)B^\\star|\*{\\op}\\le |I-\\widehat P|\*{\\op},|P^\\star-\\widehat P|\*{\\op},|B^\\star|\*{\\op}

=|P^\\star-\\widehat P|\_{\\op}.

]



\\textbf{(3) UNSURE.}\\

If the projector is fixed on the whole segment, i.e. (\\widehat P\_{s-1}\\equiv \\widehat P\_k) for all (s\\in E\_k), then

\[

|\\xi\_s|\\le |x\_s|\*2,|(I-\\widehat P\_k)\\theta\_s|\*2 \\le R\*\\mathcal A S\_w \\varepsilon\_k

]

follows exactly from claim ((2)).\\

But the lemma statement uses (a\_s^\\star=\\widehat U\*{t-1}^\\top\\theta\_s) with a \\emph{fixed} (\\widehat U\_{t-1}), while line (87) defines (\\xi\_s=x\_s^\\top(I-\\widehat P\_{s-1})\\theta\_s) with a potentially time-varying projector.\\

To decide, I need the invariant (\\widehat P\_{s-1}=\\widehat P\_{t-1}=\\widehat P\_k) on (E\_k), or at least (\\sup\_{s\\in E\_k}|P\_k^\\star-\\widehat P\_{s-1}|\_{\\op}\\le \\varepsilon\_k).



\\textbf{(4) VERIFIED.}\\

The left-hand side ((\\widehat a\_t-a\_t^\\star)^\\top z) is a scalar reward prediction error.\\

The first term has matching units because (\\beta\_t^{(r,W)}) bounds (|N\_t|\*{\\widetilde V\_t^{-1}}), and the third term has the same structure with (\\bar\\xi\_k) in place of a noise scale.\\

The middle term (R\*\\mathcal A V\_{k,t}(W)) is also scalar-reward sized, since (V\_{k,t}(W)) is a sum of parameter drifts (|a\_{s+1}^\\star-a\_s^\\star|\_2) and (|z|\*2\\le R\*\\mathcal A).



\\textbf{(5) FLAGGED.}\\

The rewrite should be

\[

B\_t^{\\mathrm{drift}}=-\\sum\_u\\Bigl(\\sum\_{s<u,;s\\in\\mathcal W\_t} z\_s z\_s^\\top\\Bigr)\\delta\_u,

]

not (-\\sum\_u \\delta\_u(\\sum\_{s<u} z\_s z\_s^\\top)); the displayed order is not matrix-compatible.\\

More seriously, (H\_u=\\widetilde V\_t^{-1/2} C,\\widetilde V\_t^{1/2}) with (C:=\\widetilde V\_t^{-1/2}(\\sum\_{s<u}z\_sz\_s^\\top)\\widetilde V\_t^{-1/2}\\preceq I) is only \\emph{similar} to (C), so this controls (\\rho(H\_u)), not (|H\_u|\*{\\op}).\\

Concrete counterexample: (\\widetilde V=\\operatorname{diag}(4,1)), (A=\\begin{psmallmatrix}2\&1\[1pt]1\&1/2\\end{psmallmatrix}\\preceq \\widetilde V); then

\[

H=\\widetilde V^{-1}A=\\begin{pmatrix}1/2\&1/4\\ 1\&1/2\\end{pmatrix}

]

has eigenvalues (1,0) but (|H|\*{\\op}=5/4>1).



\\textbf{(6) VERIFIED.}\\

Because (\\widetilde V\_t\\succ0), the map (v\\mapsto |v|\*{\\widetilde V\_t^{-1}}=|\\widetilde V\_t^{-1/2}v|\*2) is a genuine norm, so

\[

\\Bigl|\\sum\_s z\_s\\xi\_s\\Bigr|\*{\\widetilde V\_t^{-1}} \\le \\sum\_s |\\xi\_s|,|z\_s|\*{\\widetilde V\_t^{-1}}

]

is a correct triangle inequality application.\\

Then Cauchy--Schwarz gives

\[

\\sum\_{s\\in\\mathcal W\_t}|z\_s|\*{\\widetilde V\_t^{-1}}

\\le \\sqrt{W}\\Bigl(\\sum\*{s\\in\\mathcal W\_t}|z\_s|\*{\\widetilde V\_t^{-1}}^2\\Bigr)^{1/2}.

]

Finally,

\[

\\sum\*{s\\in\\mathcal W\_t}|z\_s|\*{\\widetilde V\_t^{-1}}^2

=\\operatorname{tr}!\\Bigl(\\widetilde V\_t^{-1}\\sum\*{s\\in\\mathcal W\_t} z\_s z\_s^\\top\\Bigr)

=\\operatorname{tr}(I-\\lambda \\widetilde V\_t^{-1})\\le r\\le 2rL\_W,

]

so the stated bound holds.



\\textbf{(7) FLAGGED.}\\

The summation step is correct:

\[

\\sum\_{t\\in E\_k}|z\_t|\*{\\widetilde V\_t^{-1}}

\\le \\sqrt{n\_k}\\Bigl(\\sum\*{t\\in E\_k}|z\_t|\*{\\widetilde V\_t^{-1}}^2\\Bigr)^{1/2}

\\le \\sqrt{2rn\_kL\_W},

]

hence the propagated term is exactly (2rL\_W R\*\\mathcal A S\_w\\varepsilon\_k\\sqrt{Wn\_k}).\\

But for this to be lower-order than (R\_\\mathcal A S\_w\\varepsilon\_k n\_k), one needs

\[

2rL\_W\\sqrt{Wn\_k}\\le n\_k

\\iff n\_k\\ge 4r^2L\_W^2W = W(2rL\_W)^2,

]

not (n\_k\\ge W/(2rL\_W)^2).\\

Counterexample: (r=L\_W=1), (W=16), (n\_k=4) satisfies the proof’s condition (4\\ge 4), but (2\\sqrt{Wn\_k}=16>4), so the “lower-order” claim fails.



\\textbf{(8) FLAGGED.}\\

For (f(m)=Am+B\\ell\_k m^{-1/2}), one has

\[

f'(m)=A-\\frac{1}{2}B\\ell\_k m^{-3/2},

\\qquad

f'(m)=0 \\iff m=\\Bigl(\\frac{B\\ell\_k}{2A}\\Bigr)^{2/3},

]

so the derivative calculation itself is correct.\\

However this optimizer need not lie in (\[1,\\ell\_k]): it exceeds (\\ell\_k) whenever (B>2A\\sqrt{\\ell\_k}), and it is below (1) whenever (B\\ell\_k<2A).\\

Concrete counterexample: (A=1), (B=100), (\\ell\_k=4) gives (m\_k^\\star\\approx 34.2>\\ell\_k); the theorem needs clipping by (\\min{\\ell\_k,\\max{1,\\lceil\\cdot\\rceil}}).



\\textbf{(9) VERIFIED.}\\

For (p=2/3\\in(0,1)), the concavity/power-mean inequality gives

\[

\\sum\_{k=1}^K \\ell\_k^p \\le K^{1-p}\\Bigl(\\sum\_{k=1}^K \\ell\_k\\Bigr)^p .

]

Substituting (p=2/3) and (\\sum\_k \\ell\_k=T) yields

\[

\\sum\_{k=1}^K \\ell\_k^{2/3}\\le K^{1/3}T^{2/3}.

]

This is exact and needs only (\\ell\_k\\ge 0).



\\textbf{(10) VERIFIED.}\\

The bias-floor piece is

\[

\\sum\_k R\_\\mathcal A S\_w \\Delta\_\\sigma, n\_k

= R\_\\mathcal A S\_w \\Delta\_\\sigma \\sum\_k n\_k

\\le R\_\\mathcal A S\_w \\Delta\_\\sigma, T,

]

so it is a separate additive (O(T\\Delta\_\\sigma)) term.\\

It cannot be absorbed into (O(V)), because (\\Delta\_\\sigma) is a probe-estimation bias floor and may be nonzero even when (V=0).\\

The only nit is that the proof should write (\\le T), not (=T), unless it has already shown (\\sum\_k n\_k=T).



\\textbf{(11) VERIFIED.}\\

For a width-(W) trailing window (\\mathcal W\_t={t-W+1,\\dots,t}), the edge (s\\to s+1) is included iff

\[

t-W+1\\le s

\\quad\\text{and}\\quad

s+1\\le t,

]

i.e. (t\\in{s+1,\\dots,s+W-1}).\\

Hence each edge appears in at most (W-1\\le W) windows, so (\\sum\_{k,t}V\_{k,t}(W)\\le WV).\\

Also

\[

|a\_{s+1}^\\star-a\_s^\\star|\*2

=|\\widehat U\*{t-1}^\\top(\\theta\_{s+1}-\\theta\_s)|\*2

\\le |\\theta\*{s+1}-\\theta\_s|\*2

]

because (|\\widehat U\*{t-1}|\_{\\op}=1).



\\textbf{(12) FLAGGED.}\\

The comparison (WV \\ll r\\sqrt{KT}) is the right criterion for the drift term to be lower-order, so (V=o(r\\sqrt{KT}/W)) is fine as a \\emph{regime condition}.\\

But the special claim (V\\le 2(K-1)S\_w) for “piecewise-constant subspaces” is false under the stated model (\\theta\_t=B\_k^\\star w\_t): (V) measures within-segment variation of (\\theta\_t), not only boundary jumps.\\

Counterexample: (K=1), (B\_1^\\star=e\_1), (w\_t=(-1)^tS\_w). Then the subspace is constant, yet

\[

V=\\sum\_{t=1}^{T-1}|\\theta\_{t+1}-\\theta\_t|\*2

=\\sum\*{t=1}^{T-1}2S\_w

=2S\_w(T-1),

]

not (O(KS\_w)).



\\textbf{(13) FLAGGED.}\\

The union bound arithmetic is correct:

\[

K\\cdot \\frac{\\delta}{2K}+\\frac{\\delta}{2}=\\delta,

]

and the exponents in the displayed final rate match the theorem statement syntactically.\\

However the proof chain is broken earlier: claim ((1)) has the wrong optimism sign, claim ((5)) uses an invalid (|H\_u|\*{\\op}\\le 1) inference, claim ((7)) has the wrong lower-order threshold, and claim ((8)) omits clipping of (m\_k^\\star).\\

Therefore the final theorem is \\emph{not verified} from the proof as written, even though the final displayed rate has the intended form

\[

\\widetilde O(r\\sqrt{KT})+\\widetilde O(K^{1/3}T^{2/3})+O(WV)+O(T\\Delta\*\\sigma).

]





\-------





&#x20;## Chunk A5\_\_Rank adaptive



\### Claude response

&#x20;\\textbf{Review of \\texttt{chunk\_A5\_rank\_adaptive.tex}.}



&#x20; \\bigskip



&#x20; \\textbf{(1) Weyl inequality application. \\textit{VERIFIED.}}



&#x20; Weyl for symmetric $A, A+E\\in\\mathbb R^{d\\times d}$ with eigenvalues sorted non-increasingly gives

&#x20; \[

&#x20; \\lambda\_d(E);\\le;\\lambda\_i(A+E)-\\lambda\_i(A);\\le;\\lambda\_1(E),

&#x20; ]

&#x20; so $|\\lambda\_i(A+E)-\\lambda\_i(A)|\\le\\max(|\\lambda\_1(E)|,|\\lambda\_d(E)|)=|E|{\\op}$. Setting $A=\\bar M\_k+\\widetilde B$,

&#x20; $E=\\widehat M\_k-\\bar M\_k-\\widetilde B$ yields $A+E=\\widehat M\_k$ and

&#x20; \[

&#x20; |\\lambda\_i(\\widehat M\_k)-\\lambda\_i(\\bar M\_k+\\widetilde B)|;\\le;|\\widehat M\_k-\\bar M\_k-\\widetilde B|{\\op};\\le;\\tau\_k

&#x20; ]

&#x20; on the Bernstein-good event. The index $i$ must refer to the \\emph{same sort position} on both sides (standard

&#x20; convention); the chunk says ``corresponding eigenvalue'' which I read that way. One open precondition: Weyl requires

&#x20; symmetry of $\\widehat M\_k$ and $\\bar M\_k+\\widetilde B$. Segment factorisation $B^\\star\\bar S(B^\\star)^\\top$ is

&#x20; symmetric and a scaled identity is symmetric, so this holds \\emph{provided} $G\_t$ are symmetric (PSD rank-one outers,

&#x20; or similar). If the probe ever produces asymmetric summands, one needs Wedin/Mirsky on singular values instead, and

&#x20; the argument must be restated.



&#x20; \\bigskip



&#x20; \\textbf{(2) Rank recovery. \\textit{FLAGGED.} The proof silently swaps $\\spec(\\bar M\_k+\\widetilde B)$ for $\\spec(\\bar

&#x20; M\_k)$ mid-argument. With the stated hypotheses, the claim fails for generic scaled-identity bias.}



&#x20; Weyl controls $\\lambda\_i(\\widehat M\_k)$ vs.\\ $\\lambda\_i(\\bar M\_k+\\widetilde B)$, but the chunk then writes ``the

&#x20; population spectrum of $\\bar M\_k$ has exactly $r$ eigenvalues $\\ge\\lambda\_{\\min}$ and the remaining $d-r$ are zero''

&#x20; --- that is the spectrum of $\\bar M\_k$, not of $\\bar M\_k+\\widetilde B$.



&#x20; Let $\\widetilde B=bI$ with $|b|\\le b\_\\sigma$. Then

&#x20; \[

&#x20; \\spec(\\bar M\_k+\\widetilde B)={\\lambda\_1+b,\\ldots,\\lambda\_r+b}\\cup{,b,}{\\text{repeated }d-r\\text{ times}}.

&#x20; ]

&#x20; Weyl gives

&#x20; \[

&#x20; \\text{top }r:\\ \\lambda\_i(\\widehat M\_k)\\in\[\\lambda\_i+b-\\tau\_k,\\ \\lambda\_i+b+\\tau\_k],\\quad

&#x20; \\text{bottom }d-r:\\ \\lambda\_i(\\widehat M\_k)\\in\[b-\\tau\_k,\\ b+\\tau\_k].

&#x20; ]

&#x20; For absolute-value thresholding at $2\\tau\_k$ to return exactly $r$ indices we need

&#x20; \[

&#x20; (\\text{top in}):\\ \\lambda{\\min}+b-\\tau\_k>2\\tau\_k

&#x20; \\quad\\text{AND}\\quad

&#x20; (\\text{bottom out}):\\ |b|+\\tau\_k\\le 2\\tau\_k,

&#x20; ]

&#x20; i.e., $|b|\\le\\tau\_k$, hence $b\_\\sigma\\le\\tau\_k$. This is \\emph{not} in the corollary's hypothesis.



&#x20; \\textit{Concrete counterexample.} Let $d=2$, $r=1$, $\\bar M\_k=\\diag(4\\tau\_k,0)$, $\\widetilde B=2\\tau\_k,I$ (so

&#x20; $b\_\\sigma=2\\tau\_k>\\tau\_k$), and pick $\\widehat M\_k=\\bar M\_k+\\widetilde B$ (zero Bernstein deviation --- within the

&#x20; ``prob.\\ $\\ge 1-\\delta$'' event). Eigengap hypothesis $\\lambda\_{\\min}=4\\tau\_k\\ge 4\\tau\_k$ \\emph{holds}, yet

&#x20; \[

&#x20; \\spec(\\widehat M\_k)={6\\tau\_k,;2\\tau\_k}

&#x20; ]

&#x20; and thresholding at $2\\tau\_k$ (inclusive) returns both indices, not $r=1$. A nudge $b\\mapsto 2\\tau\_k+\\varepsilon$

&#x20; breaks the strict version identically: both eigenvalues exceed $2\\tau\_k$.



&#x20; \\textit{Tightness of the constant 4 (in the $\\widetilde B=0$ case where the chunk's argument is valid).}

&#x20; \\begin{itemize}

&#x20; \\item $\\lambda\_{\\min}\\ge 4\\tau\_k$: top-$r$ $\\in\\widehat M\_k$ are $\\ge 3\\tau\_k$, bottom $\\in\[-\\tau\_k,\\tau\_k]$. Margin

&#x20; $\\tau\_k$ on each side. Works.

&#x20; \\item $\\lambda\_{\\min}\\ge 3\\tau\_k$: top-$r$ $\\ge 2\\tau\_k$, bottom $\\le\\tau\_k$. \\emph{Works} (inclusive threshold) but

&#x20; zero margin --- this is the actual tight constant.

&#x20; \\item $\\lambda\_{\\min}\\ge 2\\tau\_k$: top-$r$ $\\ge\\tau\_k$, bottom $\\in\[-\\tau\_k,\\tau\_k]$. \\textbf{Breaks}. Counterexample:

&#x20;  $\\bar M=\\diag(2\\tau\_k,0)$, $\\widehat M=\\diag(\\tau\_k,\\tau\_k)$ (achievable since $|\\widehat M-\\bar M|\_{\\op}=\\tau\_k$).

&#x20; Thresholding at $2\\tau\_k$ returns $\\emptyset$, not ${1}$.

&#x20; \\end{itemize}

&#x20; So $4$ is \\emph{not} tight; $3$ is the true edge, with $2$ failing outright.



&#x20; \\bigskip



&#x20; \\textbf{(3) Regret transfer. \\textit{UNSURE} --- need the statement of Theorem 1.}



&#x20; The reduction conditional on $\\{\\widehat r=r\\}$, Thm.\\ 1 applies verbatim'' is clean \\emph{if} none of

&#x20; $C\_{\\sub},R\_X,B,A$ nor the rate implicitly reference a known-$r$ quantity. The usual worries: \\begin{itemize} \\item

&#x20; $C\_{\\sub},R\_X$: features of the data distribution, $r$-free. Safe. \\item $B$: if this bounds the $r\\times r$ latent

&#x20; core, the numerical value is $r$-free but the underlying object lives in an $\\widehat r\\times\\widehat r$ block;

&#x20; vacuous on the event $\\widehat r=r$. \\item $A$: often scales with $r$ (e.g.\\ $\\sqrt{dr}$, $r$, $e^{O(r)}$). If the

&#x20; rate itself contains $r$, substituting $\\widehat r$ is sound only on the recovery event --- the chunk's unchanged'' is

&#x20;  then fine conditionally, but off the event there is \\emph{no} bound at all, which is exactly what the union in (4)

&#x20; pays for.

&#x20; \\item \\textbf{Data collection.} If $m\_k$ (hence $\\tau\_k$) is chosen using $\\widehat r$ at an \\emph{earlier} epoch,

&#x20; there is a circularity between the recovery event and the Bernstein deviation needed to establish it; the chunk does

&#x20; not address this. If $m\_k$ is pre-scheduled (independent of $\\widehat r$), no issue.

&#x20; \\end{itemize}

&#x20; I need Theorem 1's full statement and the exploration schedule before committing.



&#x20; \\bigskip



&#x20; \\textbf{(4) Union bound. \\textit{VERIFIED.}}



&#x20; Let $E\_1={\\widehat r\\ne r}$, $E\_2={\\text{Thm.\\ 1 conclusion fails}}$. Then

&#x20; \[

&#x20; \\Pr(E\_1\\cup E\_2)\\le\\Pr(E\_1)+\\Pr(E\_2)\\le\\delta+\\delta=2\\delta.

&#x20; ]

&#x20; ``Extra $\\delta$'' is accurate: one additional failure event of mass $\\delta$ on top of Thm.\\ 1's $\\delta$. Standard

&#x20; re-parameterisation ($\\delta\\to\\delta/2$ throughout) pays only a $\\log 2$ inside $\\tau\_k$ if one wants the final

&#x20; $1-\\delta$. No issue.



&#x20; \\bigskip



&#x20; \\textbf{(5) Variance-misspec bias. \\textit{FLAGGED.} ``Uniform shift doesn't change top-$r$'' is true for

&#x20; \\emph{ordering}, false for \\emph{absolute-level thresholding}.}



&#x20; Writing $\\bar M\_k+bI$: the shift

&#x20; \\begin{itemize}

&#x20; \\item preserves eigenvectors ($bI$ commutes with everything),

&#x20; \\item preserves the rank-order of eigenvalues (top-$k$ remains top-$k$),

&#x20; \\item preserves gaps $\\lambda\_i-\\lambda\_{i+1}$,

&#x20; \\end{itemize}

&#x20; but it does \\emph{not} preserve

&#x20; \\begin{itemize}

&#x20; \\item absolute eigenvalue magnitudes,

&#x20; \\item distance from a fixed threshold.

&#x20; \\end{itemize}

&#x20; The chunk's rule is ``keep indices with $\\lambda\_i(\\widehat M\_k)>2\\tau\_k$'' --- an absolute-level test, \\emph{not} a

&#x20; gap or ordering test. The bias is therefore \\emph{not} absorbed; it rides with the bottom $d-r$ eigenvalues from $0$

&#x20; to $b$, and once $|b|>\\tau\_k$ the bottom cluster crosses the threshold. The counterexample in (2) exhibits this

&#x20; concretely.



&#x20; The clean fixes:

&#x20; \\begin{enumerate}

&#x20; \\item Bundle $b\_\\sigma\\le\\tau\_k$ into the corollary's hypotheses (tightens the variance-misspec regime).

&#x20; \\item Replace the absolute-level rule with a gap rule: ``return the largest $j$ with $\\lambda\_j(\\widehat

&#x20; M\_k)-\\lambda\_{j+1}(\\widehat M\_k)>3\\tau\_k$.'' Then recovery depends only on the population gap, which \\emph{is}

&#x20; shift-invariant; the eigengap hypothesis $\\lambda\_{\\min}>4\\tau\_k$ then suffices independently of $b\_\\sigma$.

&#x20; \\item If $\\widetilde B$ is observable, subtract before thresholding --- but the paper does not claim it is.

&#x20; \\end{enumerate}



&#x20; \\bigskip



&#x20; \\textbf{Summary.}

&#x20; \\begin{itemize}

&#x20; \\item (1) \\textit{VERIFIED} (modulo probe symmetry).

&#x20; \\item (2) \\textit{FLAGGED}: swap of $\\spec(\\bar M+\\widetilde B)$ for $\\spec(\\bar M)$; constant 4 not tight (3 is); 2

&#x20; breaks by explicit counterexample.

&#x20; \\item (3) \\textit{UNSURE}: need Theorem 1 and the exploration schedule to confirm $r$-independence of constants and

&#x20; rule out circularity in $m\_k$.

&#x20; \\item (4) \\textit{VERIFIED}.

&#x20; \\item (5) \\textit{FLAGGED}: shift is ordering- and gap-invariant, \\emph{not} threshold-invariant.

&#x20; \\end{itemize}



&#x20; \\textbf{Single most important fix:} either add $b\_\\sigma\\le\\tau\_k$ to the hypothesis, or replace absolute-level

&#x20; thresholding by a gap rule. Without one of these, the corollary is false in the non-trivial variance-misspecified

&#x20; regime (5), which is the regime it is ostensibly designed to handle.





\### GPT response



\[

\\begin{array}{l}

\\textbf{(1) VERIFIED}\\

\\text{Let }E\_k:=\\left{\\left|\\widehat M\_k-\\left(\\bar M\_k^{\\mathrm{probe}}+\\widetilde B\\right)\\right|\_{\\op}\\le \\tau\_k\\right};\\ \\Pr(E\_k)\\ge 1-\\delta\\text{ by the stated matrix Bernstein bound.}\\

\\text{On }E\_k,\\text{ since both matrices are symmetric, Weyl gives for the eigenvalues ordered in the same nonincreasing order }\\

\\qquad |\\lambda\_i(\\widehat M\_k)-\\lambda\_i(\\bar M\_k^{\\mathrm{probe}}+\\widetilde B)|\\le \\tau\_k,\\qquad i=1,\\dots,d.\\

\\text{There is no extra correspondence subtlety beyond consistent index ordering; repeated eigenvalues do not break the bound because Weyl is index-wise, not eigenvector-wise.}

\\end{array}

]



\[

\\begin{array}{l}

\\textbf{(2) FLAGGED}\\

\\text{The failing step is the separation argument for }\\bar M\_k^{\\mathrm{probe}}\\text{ instead of }\\bar M\_k^{\\mathrm{probe}}+\\widetilde B:\\text{ Weyl controls the latter spectrum, not the former.}\\

\\text{Counterexample: }d=2,\\ r=1,\\ \\bar M\_k^{\\mathrm{probe}}=\\operatorname{diag}(4\\tau\_k,0),\\ \\widetilde B=3\\tau\_k I,\\ \\widehat M\_k=\\bar M\_k^{\\mathrm{probe}}+\\widetilde B=\\operatorname{diag}(7\\tau\_k,3\\tau\_k).\\

\\text{Then }\\left|\\widehat M\_k-(\\bar M\_k^{\\mathrm{probe}}+\\widetilde B)\\right|\*{\\op}=0,\\text{ yet thresholding at }2\\tau\_k\\text{ returns rank }2\\neq r;\\ \\text{if }\\widetilde B=0,\\ 4\\tau\_k\\text{ is sufficient but not sharp, and } \\lambda\*{\\min}>3\\tau\_k\\text{ already suffices for the threshold }2\\tau\_k.

\\end{array}

]



\[

\\begin{array}{l}

\\textbf{(3) VERIFIED}\\

\\text{The regret theorem constants shown in the paper depend on }r\\text{ through }L\_W=\\log!\\left(1+\\frac{W L\_x^2}{\\lambda r}\\right),\\ \\beta^{(r,W)},\\text{ and the }r\\text{-dimensional exploitation term.}\\

\\text{On the event }\\widehat r\_k=r,\\text{ the rank-adaptive algorithm uses exactly the same dimension as the oracle-known-}r\\text{ algorithm, so these constants become identical after substitution } \\widehat r\_k=r.\\

\\text{The remaining constants }A,\\ B,\\ C\_{\\mathrm{sub}},\\ R\_X\\text{ do not require prior knowledge of }r,\\text{ so conditional on correct rank recovery there is no additional approximation term beyond the failure event itself.}

\\end{array}

]



\[

\\begin{array}{l}

\\textbf{(4) FLAGGED}\\

\\text{The failing step is the phrase ``the bound applies unchanged'' if this is read as keeping the same }1-\\delta\\text{ confidence level: a union bound gives only }1-2\\delta.\\

\\text{Concrete counterexample: let }E\\text{ be the Theorem 1 success event and }F\\text{ the rank-recovery event, independent with }\\Pr(E)=\\Pr(F)=0.9\\ (\\delta=0.1);\\

\\text{then }\\Pr(E\\cap F)=0.81<0.9,\\text{ so the same }1-\\delta\\text{ guarantee is false unless the proof reruns both ingredients with }\\delta/2\\text{ each.}

\\end{array}

]



\[

\\begin{array}{l}

\\textbf{(5) FLAGGED}\\

\\text{Weyl itself is not harmed by the bias, because it is applied to }\\bar M\_k^{\\mathrm{probe}}+\\widetilde B,\\text{ but the corollary's thresholding argument ignores that }\\widetilde B=bI\\text{ shifts every eigenvalue by the same }b.\\

\\text{False-positive counterexample: } \\bar M\_k^{\\mathrm{probe}}=\\operatorname{diag}(4\\tau\_k,0),\\ b=3\\tau\_k,\\ \\widehat M\_k=\\operatorname{diag}(7\\tau\_k,3\\tau\_k),\\ \\text{so threshold }2\\tau\_k\\text{ returns rank }2.\\

\\text{False-negative counterexample: } b=-3\\tau\_k\\text{ gives }\\widehat M\_k=\\operatorname{diag}(\\tau\_k,-3\\tau\_k),\\text{ so threshold }2\\tau\_k\\text{ returns rank }0;\\ \\text{thus the corollary needs either }\\delta\_\\sigma=0\\text{ or an explicit bias-compensated threshold condition involving }b.

\\end{array}

]





\-----





\## Chunk A6\_\_adaptive



\### Claude response

&#x20;\\textbf{Adversarial audit of \\texttt{chunk\_A6\_adaptive.tex}}. I re-derived each claim from scratch before comparing

&#x20; with the proof. One claim checks out, one has a minor caveat, one is numerically consistent but misleading, and

&#x20; \\emph{two} are materially wrong (including claim (4), which cannot be salvaged without allowing $\\mu$ to depend on

&#x20; $(K,T)$).



&#x20; \\bigskip



&#x20; \\textbf{(1) FALSE-ALARM BOUND under $H\_0$. \\quad VERIFIED (with warm-up caveat).}



&#x20; Re-derivation. Let $M := \\mathbb E\[\\widehat M^{\\mathrm{recent}} \\mid H\_0] = \\mathbb E\[\\widehat M^{\\mathrm{past}} \\mid

&#x20; H\_0]$. Matrix Freedman on each window gives, for the \\emph{recent} half with $W\_{\\mathrm{det}}$ samples,

&#x20; $$

&#x20; \\Pr!\\left(|\\widehat M^{\\mathrm{recent}} - M|\\mathrm{op} > \\eta{\\mathrm{det}}\\right) ;\\le;

&#x20; \\frac{\\delta\_{\\mathrm{FA}}}{2T},

&#x20; \\qquad \\eta\_{\\mathrm{det}} ;=; C\_{\\mathrm{sub}}\\sqrt{\\tfrac{\\log(dT/\\delta\_{\\mathrm{FA}})}{W\_{\\mathrm{det}}}},

&#x20; $$

&#x20; and the same bound (in fact tighter) for the \\emph{past} half, since $N\_{\\mathrm{past}} \\ge W\_{\\mathrm{det}}$.

&#x20; Triangle inequality,

&#x20; $$

&#x20; S\_t ;\\le; |\\widehat M^{\\mathrm{recent}} - M|\\mathrm{op} + |\\widehat M^{\\mathrm{past}} - M|\\mathrm{op} ;\\le;

&#x20; 2\\eta\_{\\mathrm{det}},

&#x20; $$

&#x20; so the ``$2$'' in front of $\\eta\_{\\mathrm{det}}$ is \\emph{exactly} the triangle-inequality constant — correct. Union

&#x20; bound over $t=1,\\dots,T$ absorbs the extra factor $2$ into $\\log(dT/\\delta\_{\\mathrm{FA}})$. \\quad $\\checkmark$



&#x20; \\emph{Caveat.} The hypothesis $N\_{\\mathrm{past}} \\ge W\_{\\mathrm{det}}$ fails for $t - \\tau\_{k-1} <

&#x20; W\_{\\mathrm{det}}/\\mu$ rounds after a detection, when the past'' accumulation holds fewer than $W\_{\\mathrm{det}}$

&#x20; post-change probes. The proof should explicitly mute the detector during this warm-up, else $\\eta\_{\\mathrm{det}}$ is

&#x20; an under-estimate and the $2$'' becomes a lie at start-of-segment.



&#x20; \\bigskip



&#x20; \\textbf{(2) DETECTION DELAY under $H\_1$. \\quad FLAGGED — $\\mu$ is implicitly set to $1$.}



&#x20; The proof conflates \\emph{probes} and \\emph{rounds}. The recent window is defined as the last $W\_{\\mathrm{det}}$

&#x20; \\emph{probes} (line 41: last $W\_{\\mathrm{det}}$ probes''), so after the true change at round $\\tau\_k$ the window

&#x20; contains a \\emph{mixture} $$ \\widehat M^{\\mathrm{recent}}\_{\\tau\_k+s} \\;\\approx\\; \\tfrac{\\mu s}{W\_{\\mathrm{det}}}\\,

&#x20; M^{\\mathrm{post}} \\;+\\; \\tfrac{W\_{\\mathrm{det}} - \\mu s}{W\_{\\mathrm{det}}}\\, M^{\\mathrm{pre}}, \\qquad 0 \\le \\mu s \\le

&#x20; W\_{\\mathrm{det}}, $$ so the signal carried by the recent window grows linearly: $$ \\bigl\\|\\widehat M^{\\mathrm{recent}}

&#x20;  - \\widehat M^{\\mathrm{past}}\\bigr\\|\_\\mathrm{op} \\;\\approx\\; \\tfrac{\\mu s}{W\_{\\mathrm{det}}}\\,\\Delta\_k \\pm

&#x20; 2\\eta\_{\\mathrm{det}}. $$ Setting this $\\ge 2\\eta\_{\\mathrm{det}}$ (the detection threshold) and using $\\Delta\_k \\ge 2b

&#x20; > 4\\eta\_{\\mathrm{det}}$ gives $$ s \\;\\ge\\; \\frac{2\\eta\_{\\mathrm{det}}}{\\Delta\_k}\\cdot\\frac{W\_{\\mathrm{det}}}{\\mu}

&#x20; \\;\\le\\; \\frac{W\_{\\mathrm{det}}}{2\\mu}, \\qquad\\Longrightarrow\\qquad D\_k \\;=\\;

&#x20; \\Theta\\!\\left(\\frac{W\_{\\mathrm{det}}}{\\mu}\\right) \\text{ rounds}, $$ \\emph{not} $O(W\_{\\mathrm{det}})$. The stated

&#x20; bound is correct only in probes; the proof uses rounds''.



&#x20; \\emph{Concrete counterexample.} Take $W\_{\\mathrm{det}}=100$, $\\mu=10^{-2}$. The proof claims delay $\\le c\\cdot 100 =

&#x20; O(100)$ rounds. In fact the recent window cannot even be \\emph{filled} with post-change probes in under

&#x20; $W\_{\\mathrm{det}}/\\mu = 10^4$ rounds; during rounds $\\tau\_k,\\dots,\\tau\_k + 5000$ the recent window is majority

&#x20; pre-change and the signal is below threshold, so the detector cannot possibly fire. Delay is $\\ge 5000 \\gg 100$.



&#x20; \\bigskip



&#x20; \\textbf{(3) REGRET OVERHEAD $O(KW\_{\\mathrm{det}})$. \\quad FLAGGED — should be $O(KW\_{\\mathrm{det}}/\\mu)$.}



&#x20; Given (2), $\\sum\_{k=1}^K D\_k = O(KW\_{\\mathrm{det}}/\\mu)$ rounds, each contributing at most $2R\_{\\cA} S\_w = O(1)$

&#x20; instantaneous regret, so the correct overhead is

&#x20; $$

&#x20; \\mathrm{Overhead} ;=; O!\\left(\\frac{K W\_{\\mathrm{det}}}{\\mu}\\right),

&#x20; $$

&#x20; not $O(K W\_{\\mathrm{det}})$. For \\emph{fixed} $\\mu = \\Theta(1)$ the two differ only by a constant, so the big-$O$ is

&#x20; not strictly false — but it is dangerously misleading, because the optimal'' $\\mu$ (see (4)) is $\\mu \\asymp

&#x20; (K/T)^{1/3} \\to 0$, and then the $1/\\mu = (T/K)^{1/3}$ factor inflates the overhead to

&#x20; $K^{2/3}T^{1/3}W\_{\\mathrm{det}}$. That is no longer lower-order''; at $K=1$, $W\_{\\mathrm{det}}=T^{1/3}$ it is

&#x20; $T^{2/3}$, \\emph{matching} the leading rate.



&#x20; \\bigskip



&#x20; \\textbf{(4) FIXED PROBE RATE $\\mu \\in (0,1)$. \\quad FLAGGED — the claim is false for $\\mu=\\Theta(1)$.}



&#x20; This is the load-bearing claim of the theorem. I re-derive the probe/estimation trade-off from scratch.



&#x20; \\emph{Oracle rate.} For segment of length $\\ell\_k$ with $m\_k$ probes, the (Boss--Jedra / Dikkala-style) regret

&#x20; decomposes as

&#x20; $$

&#x20; \\underbrace{m\_k}{\\text{probe cost}} ;+; \\underbrace{\\frac{\\ell\_k}{\\sqrt{m\_k}}}{\\text{exploitation loss}},

&#x20; $$

&#x20; minimised at $m\_k^\\star \\asymp \\ell\_k^{2/3}$ with per-segment value $\\ell\_k^{2/3}$. Summing and using concavity of

&#x20; $x\\mapsto x^{2/3}$ with $\\sum\_k\\ell\_k = T$,

&#x20; $$

&#x20; \\sum\_{k=1}^K \\ell\_k^{2/3} ;\\le; K^{1/3}!\\left(\\sum\_k\\ell\_k\\right)^{!2/3} ;=; K^{1/3}T^{2/3}.

&#x20; $$



&#x20; \\emph{Fixed-rate allocation.} With $m\_k = \\mu \\ell\_k$ probes per segment,

&#x20; $$

&#x20; R(\\mu) ;:=; \\underbrace{\\mu T}{\\sum\_k \\mu\\ell\_k} ;+; \\underbrace{\\sum\_k

&#x20; \\frac{\\ell\_k}{\\sqrt{\\mu\\ell\_k}}}{=\\sum\_k\\sqrt{\\ell\_k/\\mu}}

&#x20; ;\\le; \\mu T + \\sqrt{\\tfrac{KT}{\\mu}}

&#x20; $$

&#x20; (the inequality by Cauchy–Schwarz: $\\sum\_k\\sqrt{\\ell\_k} \\le \\sqrt{K\\sum\_k\\ell\_k} = \\sqrt{KT}$).



&#x20; \\emph{Minimising over $\\mu$.} Setting $\\partial\_\\mu R = 0$:

&#x20; $$

&#x20; T ;=; \\tfrac{1}{2}\\sqrt{KT},\\mu^{-3/2}

&#x20; \\quad\\Longrightarrow\\quad

&#x20; \\mu^\\star ;=; \\Bigl(\\tfrac{K}{4T}\\Bigr)^{1/3} ;\\asymp; (K/T)^{1/3}.

&#x20; $$

&#x20; At $\\mu^\\star$, both terms equal $\\Theta(K^{1/3}T^{2/3})$, matching oracle. $\\checkmark$ \\emph{There is a unique

&#x20; exponent of $T$ that works, and it is not a constant.}



&#x20; \\emph{The decisive counterexample.} Fix \\emph{any} $\\mu\\in(0,1)$ independent of $K,T$ and take $K=1$, $T\\to\\infty$:

&#x20; $$

&#x20; \\frac{R(\\mu)}{R^\\star} ;=; \\frac{\\mu T + \\sqrt{T/\\mu}}{\\ T^{2/3}} ;\\sim; \\mu,T^{1/3} ;\\xrightarrow\[T\\to\\infty]{};

&#x20; \\infty.

&#x20; $$

&#x20; So for $K=1$, $\\mu=1/2$:

&#x20; $$

&#x20; R(\\tfrac12) ;\\ge; \\tfrac12 T \\quad\\text{vs.}\\quad R^\\star ;=; \\Theta(T^{2/3}),

&#x20; $$

&#x20; a factor $\\Theta(T^{1/3})$ gap — \\emph{not} a constant, \\emph{not} poly-log, but a polynomial-in-$T$ blow-up. The

&#x20; claim at most a constant factor in the leading rate'' is therefore \\textbf{false} under the theorem's own wording

&#x20; (fixed $\\mu \\in (0,1)$'').



&#x20; \\emph{Diagnosis / minimal fix.} The theorem is recoverable if one of the following is adopted:

&#x20; \\begin{itemize}

&#x20; \\item Declare $\\mu = \\mu(K,T) = \\Theta((K/T)^{1/3})$; then $R = \\Theta(K^{1/3}T^{2/3})$ and the theorem is

&#x20; rate-optimal, but the algorithm is \\emph{no longer independent of $T,K$} — contradicting the motivation on line 34

&#x20; (does not require segment lengths $\\ell\_k$''). Note it still does not need $\\ell\_k$, only $T$ and $K$, so the selling

&#x20; point is partially preserved. \\item Keep $\\mu$ constant and replace the stated rate in Theorem\~1 by $\\tilO(r\\sqrt{KT})

&#x20;  + \\tilO(\\mu T + \\sqrt{KT/\\mu})$, which is $\\Theta(T)$ for $\\mu = \\Theta(1)$ — honest but embarrassing. \\item Make

&#x20; $\\mu$ data-adaptive (e.g.\\ doubling trick on $T$, or a rate that decays with the empirical round index). But then

&#x20; fixed $\\mu$'' is a misnomer.

&#x20; \\end{itemize}



&#x20; Also flagged as a side-effect of (4): the proof re-uses Theorem\~1's $\\tilO(K^{1/3}T^{2/3})$ term \\emph{verbatim} (line

&#x20;  59), which was derived under the \\emph{oracle} schedule $m\_k \\asymp \\ell\_k^{2/3}$. That derivation does not carry

&#x20; through when probes are Bernoulli-$\\mu$. The sentence ``bound of Theorem\~1 carries through per-segment'' is doing all

&#x20; the work and is unsupported.



&#x20; \\bigskip



&#x20; \\textbf{(5) INHERITED BIAS FLOOR $O(T\\Delta\_\\sigma)$. \\quad VERIFIED.}



&#x20; $\\Delta\_\\sigma$ is a per-round model-misspecification bias. Summing over the horizon yields $T\\Delta\_\\sigma$

&#x20; regardless of how segment boundaries are estimated, as long as the bias is a property of the \\emph{action-reward

&#x20; model}, not the subspace estimate. The detector does not couple to $\\Delta\_\\sigma$, so this term is unaffected by the

&#x20; adaptive layer. $\\checkmark$



&#x20; \\bigskip



&#x20; \\textbf{(6) SEPARATION ASSUMPTION $\\Delta\_k \\ge 2b$. \\quad FLAGGED — no graceful degradation.}



&#x20; The theorem assumes $\\Delta\_k \\ge 2b$ for \\emph{all} $k$; the proof says nothing about what happens otherwise.

&#x20; Concretely, if $\\Delta\_{k\_0} < 2b$ at some boundary, the detector may never fire on segment $k\_0$ (under $H\_0$-like

&#x20; statistics), and SPSC-Adaptive will continue using the stale subspace $\\widehat P\_{k\_0-1}$ throughout segment $k\_0$,

&#x20; accruing

&#x20; $$

&#x20; \\text{regret on missed segment} ;=; \\Theta\\bigl(\\ell\_{k\_0}\\cdot \\Delta\_{k\_0}^2\\bigr)

&#x20; $$

&#x20; (squared, since regret from subspace mismatch is second-order in the operator-norm gap, under the usual quadratic

&#x20; reward model). A complete theorem should therefore include a term

&#x20; $$

&#x20; \\sum\_{k:\\ \\Delta\_k < 2b} \\ell\_k,\\min\\bigl(\\Delta\_k^2,, 1\\bigr),

&#x20; $$

&#x20; or an assumption that rules it out with a witness. As stated the bound is \\emph{vacuous} whenever any $\\Delta\_k \\in

&#x20; \[0, 2b)$; there is no witness.



&#x20; Second issue: the bound $b > 2\\eta\_{\\mathrm{det}}$ plus $\\Delta\_k \\ge 2b$ means $\\Delta\_k \\ge 4\\eta\_{\\mathrm{det}}$; I

&#x20;  used this in (2) to claim $D\_k \\le W\_{\\mathrm{det}}/(2\\mu)$. If one only has $\\Delta\_k \\ge 2b$ with $b =

&#x20; 2\\eta\_{\\mathrm{det}} + \\varepsilon$ for small $\\varepsilon$, then the delay constant blows up as $1/\\varepsilon$. The

&#x20; theorem should state $\\Delta\_k \\ge c,\\eta\_{\\mathrm{det}}$ for an explicit $c > 4$, or otherwise the $O(\\cdot)$ hides

&#x20; an arbitrarily large constant.



&#x20; \\bigskip



&#x20; \\textbf{Summary verdict.}



&#x20; \\begin{tabular}{ll}

&#x20; (1) False-alarm \& \\textbf{VERIFIED} (fix warm-up masking). \\

&#x20; (2) Delay ``$O(W\_{\\mathrm{det}})$ rounds'' \& \\textbf{FLAGGED}: true delay is $\\Theta(W\_{\\mathrm{det}}/\\mu)$ rounds. \\

&#x20; (3) Overhead $O(KW\_{\\mathrm{det}})$ \& \\textbf{FLAGGED}: should be $O(KW\_{\\mathrm{det}}/\\mu)$. \\

&#x20; (4) Fixed-$\\mu$ preserves leading rate \& \\textbf{FLAGGED (fatal)}: $R(\\mu)\\ge\\mu T = \\Theta(T)$ for $\\mu=\\Theta(1)$, a

&#x20;  $\\Theta(T^{1/3})$ blow-up over $K^{1/3}T^{2/3}$. Only $\\mu \\asymp (K/T)^{1/3}$ recovers the oracle rate. \\

&#x20; (5) $T\\Delta\_\\sigma$ bias floor \& \\textbf{VERIFIED}. \\

&#x20; (6) $\\Delta\_k \\ge 2b$ assumption \& \\textbf{FLAGGED}: no bound under violation; delay constant depends on $\\Delta\_k -

&#x20; 4\\eta\_{\\mathrm{det}}$. \\

&#x20; \\end{tabular}



&#x20; \\bigskip



&#x20; The theorem as written cannot stand. The clearest repair is to replace the phrase \\emph{fixed probe rate $\\mu \\in

&#x20; (0,1)$''} with \\emph{probe rate $\\mu = c,(K/T)^{1/3}$ for a tuning constant $c>0$''}, restate the delay bound in

&#x20; probes (or explicitly as $D\_k = O(W\_{\\mathrm{det}}/\\mu)$ rounds), and add a clause for missed detections.







\### GPT response







\[

\\textbf{(1) FALSE-ALARM BOUND UNDER }H\_0

]



\[

\\text{FLAGGED}

]



\[

\\begin{aligned}

\&\\text{The valid substeps are: } {S\_t>2\\eta}\\subseteq {|A|\*{\\op}>\\eta}\\cup{|B|\*{\\op}>\\eta}, \\text{ so the prefactor }2\\text{ is correct for a triangle-inequality proof,}\\

\&\\text{and } T\\cdot(\\delta\_{\\mathrm{FA}}/T)=\\delta\_{\\mathrm{FA}} \\text{ is a correct union bound. The failing step is the calibration of } \\eta\_{\\mathrm{det}}:\\

\&\\text{the proof text defines }S\_t\\text{ using the last }W\_{\\mathrm{det}}\\text{ probes versus a segment accumulation, but then says “applied to each half,” and if each half has }W\_{\\mathrm{det}}/2\\text{ probes, the scale is }\\sqrt{2/W\_{\\mathrm{det}}},\\

\&\\text{not }1/\\sqrt{W\_{\\mathrm{det}}}\\text{ unless }C\_{\\mathrm{sub}}\\text{ is explicitly enlarged. A concrete scalar counterexample is }d=1,\\ A,B\\sim N(0,2/W\_{\\mathrm{det}}):\\

\&\\text{then }A-B\\sim N(0,4/W\_{\\mathrm{det}}),\\text{ so a threshold }2C\_{\\mathrm{sub}}\\sqrt{\\log/W\_{\\mathrm{det}}}\\text{ uses the wrong variance proxy if }C\_{\\mathrm{sub}}\\text{ came from a size-}W\_{\\mathrm{det}}\\text{ bound.}

\\end{aligned}

]



&#x20;



\[

\\textbf{(2) DETECTION DELAY UNDER }H\_1

]



\[

\\text{FLAGGED}

]



\[

\\begin{aligned}

\&\\text{The failing step is “}\\Delta\_k\\ge 2b \\text{ with } b>2\\eta\_{\\mathrm{det}} \\text{ forces triggering within }D\_k=O(W\_{\\mathrm{det}})\\text{ rounds.”}\\

\&\\text{If }q\\text{ post-change probes have entered the recent window, its mean shift is only }(q/W\_{\\mathrm{det}})\\Delta\_k,\\text{ so to exceed threshold }b\\text{ under }2\\eta\_{\\mathrm{det}}\\text{ noise one needs}\\

\&\\qquad q ;\\ge; W\_{\\mathrm{det}}\\frac{b+2\\eta\_{\\mathrm{det}}}{\\Delta\_k}.\\

\&\\text{Thus the probe delay is } \\Omega(W\_{\\mathrm{det}})\\text{ in the worst case }(\\Delta\_k=2b,\\ b\\downarrow 2\\eta\_{\\mathrm{det}}),\\text{ and the round delay is } \\Omega(W\_{\\mathrm{det}}/\\mu),\\

\&\\text{because probes arrive only on a }\\mu\\text{-fraction of rounds. Concrete counterexample: deterministic probing every }1/\\mu\\text{ rounds with }\\mu=1/W\_{\\mathrm{det}};\\

\&\\text{even with zero noise and }\\Delta\_k=2b,\\text{ one needs nearly }W\_{\\mathrm{det}}\\text{ post-change probes, hence delay }\\Omega(W\_{\\mathrm{det}}^2)\\text{ rounds, not }O(W\_{\\mathrm{det}}).

\\end{aligned}

]



&#x20;



\[

\\textbf{(3) REGRET OVERHEAD } O(KW\_{\\mathrm{det}})

]



\[

\\text{FLAGGED}

]



\[

\\begin{aligned}

\&\\text{The failing step is the substitution }2R\_{\\mathcal A}S\_w\\sum\_k D\_k = O(KW\_{\\mathrm{det}})\\text{ without tracking the probe-rate dependence from Claim (2).}\\

\&\\text{If }D\_k=\\Theta(W\_{\\mathrm{det}}/\\mu),\\text{ then the same line gives }2R\_{\\mathcal A}S\_w\\sum\_k D\_k = \\Theta(KW\_{\\mathrm{det}}/\\mu).\\

\&\\text{Concrete counterexample: choose } \\mu=T^{-1/3}\\text{ (fixed over time but horizon-dependent). Then the overhead is } \\Theta(KW\_{\\mathrm{det}}T^{1/3}),\\

\&\\text{which is not }O(KW\_{\\mathrm{det}})\\text{ with a }T\\text{-independent constant. The theorem is only salvageable here if it explicitly assumes } \\mu=\\Theta(1)\\text{ bounded away from }0.

\\end{aligned}

]



&#x20;



\[

\\textbf{(4) FIXED PROBE RATE VS ORACLE ALLOCATION}

]



\[

\\text{FLAGGED}

]



\[

\\begin{aligned}

\&\\text{This is the main bug. The theorem claims the adaptive variant uses a fixed } \\mu\\in(0,1)\\text{ and still achieves the same leading }T^{2/3}\\text{ rate.}\\

\&\\text{But on a segment of length }\\ell\_k,\\text{ fixed-rate probing gives }m\_k\\approx \\mu\\ell\_k,\\text{ whereas the oracle allocation is }m\_k^\\star\\asymp \\ell\_k^{2/3};\\

\&\\text{these differ by } \\ell\_k^{1/3}, \\text{ not a constant factor. Summing the fixed-rate cost gives } A\\mu T + B\\sqrt{KT/\\mu}.\\

\&\\text{Concrete counterexample: }K=1,\\ \\ell\_1=T,\\ \\mu=\\tfrac12.\\text{ Then the fixed-rate cost is } \\tfrac{A}{2}T + B\\sqrt{2T} = \\Theta(T),\\

\&\\text{while the oracle cost is } \\Theta(T^{2/3}). \\text{ To recover }T^{2/3}\\text{ one must choose } \\mu \\asymp (K/T)^{1/3}\\text{ (up to constants), not a constant } \\mu.

\\end{aligned}

]



&#x20;



\[

\\textbf{(5) INHERITED BIAS FLOOR } O(T\\Delta\_\\sigma)

]



\[

\\text{UNSURE}

]



\[

\\begin{aligned}

\&\\text{To decide this, I need the exact theorem-1 decomposition of the }O(T\\Delta\_\\sigma)\\text{ term, and the precise reset/recovery mechanics after detection and after false alarms.}\\

\&\\text{Right now the proof only says the theorem-1 bound “carries through per-segment,” but the adaptive segments are estimated, and during }\[\\tau\_k,\\widehat\\tau\_k)\\text{ a single estimated segment}\\

\&\\text{contains two different regimes. Without the theorem-1 hypotheses and the recovery-phase analysis, I cannot prove that no additional contamination term appears beyond }O!\\left(\\sum\_k D\_k\\right).

\\end{aligned}

]



&#x20;



\[

\\textbf{(6) SEPARATION ASSUMPTION } \\Delta\_k \\ge 2b

]



\[

\\text{FLAGGED}

]



\[

\\begin{aligned}

\&\\text{The theorem silently assumes away missed changes: there is no fallback bound and no explicit missed-detection regret term if some change has } \\Delta\_k<2b.\\

\&\\text{Concrete counterexample: }d=1,\\text{ one change at }T/2,\\text{ zero noise, detector threshold }b,\\text{ and actual jump } \\Delta\_k=b/2. \\text{ Then the detector never fires,}\\

\&\\text{yet if the stale subspace incurs any constant per-round loss }c>0\\text{ after the change, the extra regret is } cT/2 = \\Omega(T). \\text{ So outside the separation regime the theorem gives no protection.}

\\end{aligned}

]



&#x20;



\[

\\textbf{Bottom line:}

\\qquad

\\text{Claim (4) is definitely broken as stated. Claims (2) and (3) also break unless the theorem tracks } \\mu \\text{ explicitly or assumes } \\mu=\\Theta(1).

\\qquad

\\text{Claim (1) has a real constant/window-definition bug.}

]











\-------



\####chunk\_A7\_regret\_lb



\### Claude response

&#x20; \\textbf{(1) Construction validity — UNSURE.}



&#x20; The instance $\\theta^{(0)}\\equiv 0$ is obtained as the limit $\\Sigma\_\\eta\\to 0^+$ with $w\_0=0$. If the paper's LDS

&#x20; model requires $\\Sigma\_\\eta\\succ 0$ strictly, then $\\theta^{(0)}\\equiv 0$ lives on the boundary, not in the admissible

&#x20;  class. The standard rescue is a continuity argument: for any $\\varepsilon>0$, pick $\\Sigma\_\\eta=\\delta(T)\\cdot I$

&#x20; small enough that

&#x20; \[

&#x20; \\bigl|\\E\_\\nu\[\\DynReg\_T^{(c)}]\\big|{\\theta^{(0)}\\equiv 0}-\\E\\nu\[\\DynReg\_T^{(c)}]\\big|{\\Sigma\\eta=\\delta(T)

&#x20; I}\\bigr|<\\varepsilon,

&#x20; ]

&#x20; then transfer the bound inward. This needs

&#x20; \\begin{enumerate}

&#x20;   \\item joint continuity of $\\mathrm{KL}$ and $\\E\[\\DynReg\_T]$ at $\\Sigma\_\\eta=0$,

&#x20;   \\item uniform bound on the error across policies (we need $\\inf\_\\pi$).

&#x20; \\end{enumerate}

&#x20; The chunk asserts both without proof (``the bound is continuous in $\\Sigma\_\\eta$''). Whether this is rigorous depends

&#x20; on the exact LDS specification in the main text. \\textbf{Need:} the model section's definition of admissible

&#x20; $\\Sigma\_\\eta$ to rule out (or rescue) this. If $\\Sigma\_\\eta\\succeq 0$ is allowed, the issue is moot.



&#x20; \\medskip

&#x20; \\textbf{(2) Step 1 linear regret — VERIFIED.}



&#x20; Re-derive. Under $\\nu\_1$, reward $=x\_t^\\top(\\alpha v)=\\alpha x\_t^\\top v$. Projector symmetry $\\widehat

&#x20; P\_t^\\top=\\widehat P\_t$ and idempotence $\\widehat P\_t^2=\\widehat P\_t$ give

&#x20; \[

&#x20; x\_t^\\top v ;=; (\\widehat P\_t x\_t)^\\top v ;=; x\_t^\\top \\widehat P\_t v.

&#x20; ]

&#x20; Cauchy--Schwarz and $|x\_t|\\le R\_\\cA$: $|x\_t^\\top\\widehat P\_t v|\\le R\_\\cA|\\widehat P\_t v|$. Optimal $\\nu\_1$ reward is

&#x20; $\\sup\_{|x|\\le R\_\\cA}\\alpha,x^\\top v = R\_\\cA\\alpha$. Hence

&#x20; \[

&#x20; \\Delta\_t^{(1)} ;\\ge; R\_\\cA\\alpha - R\_\\cA\\alpha|\\widehat P\_t v| ;=; R\_\\cA\\alpha\\bigl(1-|\\widehat P\_t v|\\bigr),

&#x20; ]

&#x20; linear in $\\alpha$. The old $\\alpha^2/|w|$ artifact arose when $\\nu\_0$ had signal $|w|\\neq 0$ (generic direction) —

&#x20; making the optimal arms on $\\nu\_0,\\nu\_1$ close, collapsing the separation to quadratic order. Here $\\theta^{(0)}\\equiv

&#x20;  0$, the $\\nu\_0$ optimum is arbitrary direction with reward $0$, and the separation to any $R\_\\cA\\alpha$-direction on

&#x20; $\\nu\_1$ is unambiguously linear. Fix confirmed.



&#x20; \\medskip

&#x20; \\textbf{(3) KL chain rule — VERIFIED.}



&#x20; The chain rule for KL of sequential observations (exchangeable filtrations, deterministic policy given history) is

&#x20; \[

&#x20; \\mathrm{KL}(\\P\_0^\\cH|\\P\_1^\\cH) ;=; \\E\_{\\P\_0}!\\Bigl\[\\textstyle\\sum\_t

&#x20; \\mathrm{KL}\\bigl(\\P\_0(y\_t\\mid\\cH\_{t-1}),\\big|,\\P\_1(y\_t\\mid\\cH\_{t-1})\\bigr)\\Bigr].

&#x20; ]

&#x20; Conditionally on $\\cH\_{t-1}$, $y\_t\\sim\\cN(x\_t^\\top\\theta,\\sigma\_\\varepsilon^2)$ with $\\theta\\in{0,\\alpha v}$. Gaussian

&#x20;  KL: $(\\mu\_0-\\mu\_1)^2/(2\\sigma\_\\varepsilon^2) = \\alpha^2(x\_t^\\top v)^2/(2\\sigma\_\\varepsilon^2)$. The outer expectation

&#x20;  is under $\\P\_0$ (\\emph{first} argument of $\\mathrm{KL}$), which matters because under $\\P\_0$ the law of $\\widehat

&#x20; P\_t$ is $v$-independent. Expression matches the chunk.



&#x20; \\medskip

&#x20; \\textbf{(4a) Averaging lemma — VERIFIED.}



&#x20; For $v\\sim\\mathrm{Unif}(\\mathbb S^{d-1})$, $\\E\[vv^\\top]=I/d$. Projector $\\widehat P\_t$ symmetric idempotent:

&#x20; \[

&#x20; \\E\_v|\\widehat P\_t v|^2 = \\E\_v\[v^\\top\\widehat P\_t^\\top\\widehat P\_t v] = \\E\_v\[v^\\top\\widehat P\_t v] =

&#x20; \\mathrm{tr}(\\widehat P\_t\\cdot I/d) = \\mathrm{tr}(\\widehat P\_t)/d = r/d.

&#x20; ]



&#x20; \\medskip

&#x20; \\textbf{(4b) Adversarial $v^\\star$ — VERIFIED, phrasing misleading.}



&#x20; The substantive claim

&#x20; \[

&#x20; \\min\_{|v|=1};\\E\_{\\P\_0}!\\Bigl\[\\textstyle\\sum\_{t\\in\\cT\_{\\exp}}|\\widehat P\_t v|^2\\Bigr] ;\\le; \\frac{(T-m)r}{d}

&#x20; ]

&#x20; follows because, by Fubini on nonnegatives,

&#x20; \[

&#x20; \\E\_v!\\Bigl\[\\E\_{\\P\_0}!\\Bigl\[\\textstyle\\sum\_t|\\widehat P\_t v|^2\\Bigr]\\Bigr]

&#x20; = \\E\_{\\P\_0}!\\Bigl\[\\textstyle\\sum\_t \\E\_v|\\widehat P\_t v|^2\\Bigr]

&#x20; = \\E\_{\\P\_0}!\\Bigl\[\\textstyle\\sum\_t \\mathrm{tr}(\\widehat P\_t)/d\\Bigr]

&#x20; = (T-m)r/d,

&#x20; ]

&#x20; and $\\min\_v\\le\\E\_v$. This is what we want: \\emph{one} fixed $v^\\star$ (adversarial but non-adaptive in time) achieving

&#x20;  the sum bound.



&#x20; \\textbf{However}, the chunk's transitional sentence \\emph{the minimum over $v$ is $\\le r/d$ per round}'' is literally

&#x20; the wrong statement. Per-round $\\min\_v$ gives a $v\_t$ that depends on $t$, which is \\emph{not} an adversarial instance

&#x20;  (the adversary picks one $v$, not a sequence). The correct chain is \\\[ \\min\_v \\textstyle\\sum\_t \\E\\|\\widehat P\_t v\\|^2

&#x20;  \\;\\le\\; \\E\_v\\sum\_t\\E\\|\\widehat P\_t v\\|^2 \\;=\\; \\sum\_t r/d, \\] i.e., $\\min$ of the sum $\\le$ average of the sum,'' not

&#x20;  ``sum of per-round minima.'' The proof reaches the correct endpoint, but one sentence is sloppy and should be

&#x20; rewritten to avoid confusing a referee. \\textbf{Recommend editorial fix.}



&#x20; \\medskip

&#x20; \\textbf{(5) Step 3 Pinsker — FLAGGED (numeric slack, argument survives).}



&#x20; With the stated $\\alpha^2=\\sigma\_\\varepsilon^2/\\bigl\[4(m+R\_\\cA^2(T-m)r/d)\\bigr]$,

&#x20; \[

&#x20; \\mathrm{KL} ;\\le; \\frac{\\alpha^2}{2\\sigma\_\\varepsilon^2}\\bigl(m+R\_\\cA^2(T-m)r/d\\bigr) ;=; \\frac{1}{2\\cdot 4} ;=;

&#x20; \\frac18.

&#x20; ]

&#x20; Pinsker (standard form: $d\_{\\mathrm{TV}}\\le\\sqrt{\\mathrm{KL}/2}$, with TV as $\\tfrac12|P-Q|1=\\sup\_A|P(A)-Q(A)|$):

&#x20; \[

&#x20; d{\\mathrm{TV}} ;\\le; \\sqrt{\\tfrac{1}{8}/2} ;=; \\sqrt{\\tfrac1{16}} ;=; \\tfrac14 ;=; 0.25.

&#x20; ]

&#x20; The chunk states $d\_{\\mathrm{TV}}\\le 1/\\sqrt 8 \\approx 0.354$. The two are inconsistent; $\\tfrac14<\\tfrac{1}{\\sqrt

&#x20; 8}$, so the chunk's number is a valid but \\emph{loose} upper bound. Most likely diagnosis: the author mis-applied

&#x20; Pinsker as $d\_{\\mathrm{TV}}\\le\\sqrt{\\mathrm{KL}}$ (missing the $1/\\sqrt 2$), giving $\\sqrt{1/8}=1/\\sqrt 8$. Not a

&#x20; logical bug.



&#x20; Does it matter? The argument requires $d\_{\\mathrm{TV}}<\\tfrac12$. Both $\\tfrac14$ and $\\tfrac{1}{\\sqrt 8}\\approx

&#x20; 0.354$ satisfy this, so Le Cam's two-point method closes either way. \\textbf{Recommend: replace $1/\\sqrt 8$ with $1/4$

&#x20;  to tighten and remove the arithmetic error.} Downstream constants improve: e.g., $1-\\sqrt{r/d}-d\_{\\mathrm{TV}}\\ge

&#x20; \\tfrac34-o(1)$ instead of $\\tfrac{\\sqrt 8 - 1}{\\sqrt 8}-o(1)\\approx 0.646$.



&#x20; \\medskip

&#x20; \\textbf{(6) Step 4 positivity — VERIFIED.}



&#x20; For $d\\ge d\_0 r,T^{1/3}$, $\\sqrt{r/d}\\le 1/\\sqrt{d\_0 T^{1/3}}\\to 0$ as $T\\to\\infty$. Combined with

&#x20; $d\_{\\mathrm{TV}}\\le\\tfrac14$ (using the corrected Pinsker number) or $1/\\sqrt 8$,

&#x20; \[

&#x20; 1-\\sqrt{r/d}-d\_{\\mathrm{TV}} ;\\ge; \\tfrac34 - o(1) \\quad(\\text{or }0.646-o(1)).

&#x20; ]

&#x20; One technical point: Step 1 gives per-round $\\Delta\_t^{(1)}\\ge R\_\\cA\\alpha(1-|\\widehat P\_t v^\\star|)$, so the exploit

&#x20; regret on $\\nu\_1$ is

&#x20; \[

&#x20; R\_\\cA\\alpha,\\E\_{\\nu\_1}!\\Bigl\[\\textstyle\\sum\_{t\\in\\cT\_{\\exp}}(1-|\\widehat P\_t v^\\star|)\\Bigr] ;\\ge;

&#x20; R\_\\cA\\alpha\\bigl\[(T-m)-\\E\_{\\nu\_1}\\sum\_t|\\widehat P\_t v^\\star|\\bigr].

&#x20; ]

&#x20; Two transfers are needed:

&#x20; \\begin{itemize}

&#x20;   \\item $\\E\_{\\nu\_0}\\sum\_t|\\widehat P\_t v^\\star|\\le\\sqrt{(T-m)\\cdot(T-m)r/d}=(T-m)\\sqrt{r/d}$ (Cauchy--Schwarz + Jensen

&#x20;  on the Step-2 sum bound);

&#x20;   \\item $\\E\_{\\nu\_1}\\sum\_t|\\widehat P\_t v^\\star| - \\E\_{\\nu\_0}\\sum\_t|\\widehat P\_t v^\\star|\\le (T-m),d\_{\\mathrm{TV}}$,

&#x20; using that the summand is in $\[0,T-m]$.

&#x20; \\end{itemize}

&#x20; Both steps are standard; the chunk's one-line invocation ``$1-\\sqrt{r/d}-d\_{\\mathrm{TV}}$'' compresses them correctly.

&#x20;  Positivity $c\_1>0$ is established in the regime.



&#x20; \\medskip

&#x20; \\textbf{(7) Balancing exponents — VERIFIED.}



&#x20; With $R(m):=cm+c\_1 R\_\\cA\\sigma\_\\varepsilon T/\\sqrt m$,

&#x20; \[

&#x20; R'(m)=c-\\tfrac{c\_1 R\_\\cA\\sigma\_\\varepsilon T}{2 m^{3/2}}=0 \\quad\\Longrightarrow\\quad m^\\star = \\Bigl(\\tfrac{c\_1

&#x20; R\_\\cA\\sigma\_\\varepsilon T}{2c}\\Bigr)^{2/3} =\\Theta!\\bigl((R\_\\cA\\sigma\_\\varepsilon T/c)^{2/3}\\bigr),

&#x20; ]

&#x20; and $R(m^\\star)=\\Theta(c^{1/3}(R\_\\cA\\sigma\_\\varepsilon)^{2/3} T^{2/3})$. Both branches $cm^\\star$ and

&#x20; $R\_\\cA\\sigma\_\\varepsilon T/\\sqrt{m^\\star}$ yield the same order, confirming exponents.



&#x20; \\textbf{Caveat (not a bug).} The Step-4 regime assumption was $m\\ge T^{2/3}/d\_0$. The optimum $m^\\star\\gtrsim

&#x20; T^{2/3}/d\_0$ iff $c\\lesssim R\_\\cA\\sigma\_\\varepsilon d\_0^{3/2}$. If $c$ is too large, $m^\\star<T^{2/3}/d\_0$ and the

&#x20; balancing is clipped at $m=T^{2/3}/d\_0$, where

&#x20; \[

&#x20; cm+c\_1 R\_\\cA\\sigma\_\\varepsilon T/\\sqrt m ;=; cT^{2/3}/d\_0 + c\_1 R\_\\cA\\sigma\_\\varepsilon\\sqrt{d\_0},T^{2/3}

&#x20; ;=;\\Theta(T^{2/3}).

&#x20; ]

&#x20; The $T^{2/3}$ rate is preserved, but the stated constant $c\_0=c\_0(R\_\\cA,\\sigma\_\\varepsilon,d\_0)$ needs to absorb the

&#x20; $c$-dependent regime switch. Theorem statement \\emph{does} absorb this into $c\_0$, so the claim stands.

&#x20; \\textbf{Recommend: add one sentence acknowledging the regime clipping.}



&#x20; \\medskip

&#x20; \\textbf{(8) Small-$d$ degradation — VERIFIED (with implicit assumption).}



&#x20; For $d=\\Theta(r)$, $r/d=\\Theta(1)$, so $R\_\\cA^2(T-m)r/d=\\Theta(T-m)$ and $\\alpha\\asymp\\sigma\_\\varepsilon/\\sqrt T$.

&#x20; Exploit regret $\\asymp R\_\\cA\\sigma\_\\varepsilon\\sqrt T$, plus probe cost $cm$. Minimizing over $m$ gives $m=O(1)$ and

&#x20; total $\\Omega(\\sqrt T)$, as claimed.



&#x20; \\textbf{But}: this requires $1-\\sqrt{r/d}-d\_{\\mathrm{TV}}\\ge c\_1'>0$. At $d=r$, $\\sqrt{r/d}=1$ and the bracket is $\\le

&#x20;  0$: the construction gives the \\emph{trivial} zero lower bound, not $\\sqrt T$. For $d=\\kappa r$ with $\\kappa$ a large

&#x20;  enough constant (specifically $\\kappa > (1-d\_{\\mathrm{TV}})^{-2}\\approx 1.78$ using $d\_{\\mathrm{TV}}=1/4$), the

&#x20; bracket is positive and $\\Omega(\\sqrt T)$ holds. The remark as written is correct only for $d\\ge Cr$ with $C$ large

&#x20; enough, not for all $d=O(r)$. \\textbf{Recommend: sharpen the remark to ``for $d=\\Theta(r)$ with sufficiently large

&#x20; constant.''}



&#x20; \\medskip

&#x20; \\textbf{(9) Scope/class — VERIFIED (minor phrasing).}



&#x20; The HP assumption is used exactly once: $x\_t=\\widehat P\_t x\_t$ gives $x\_t^\\top v=x\_t^\\top\\widehat P\_t v$, bounding

&#x20; per-round exploit KL contribution by $R\_\\cA^2|\\widehat P\_t v|^2$ instead of $R\_\\cA^2$ (factor $r/d$ reduction). For

&#x20; $\\pi\\notin\\Pi\_{\\mathrm{HP}}$, $x\_t$ can place mass outside $\\mathrm{range}(\\widehat P\_t)$, so $|x\_t^\\top v|$ can reach

&#x20;  $R\_\\cA$ per round, inflating the KL upper bound by $d/r$. This relaxes the Pinsker constraint on $\\alpha$ (allows

&#x20; larger $\\alpha$), which via Step 1 would \\emph{increase} the exploit regret lower bound — but the KL ceiling now

&#x20; admits algorithms that obtain more information per exploit round, so the lower bound in this proof no longer binds

&#x20; them. Algorithms outside $\\Pi\_{\\mathrm{HP}}$ could therefore in principle beat $T^{2/3}$. Remark is correct; wording

&#x20; ``contribute additional exploit KL'' is accurate but terse.



&#x20; \\medskip

&#x20; \\textbf{Summary of actionable items:}

&#x20; \\begin{enumerate}

&#x20;   \\item \\textbf{(5)} Replace $d\_{\\mathrm{TV}}\\le 1/\\sqrt 8$ with $d\_{\\mathrm{TV}}\\le 1/4$ (and propagate to (6)).

&#x20; Arithmetic error, not a logical bug.

&#x20;   \\item \\textbf{(4b)} Rewrite the minimum over $v$ is $\\le r/d$ per round'' sentence as $\\min\_v$ of the sum is at most

&#x20;  the $v$-average of the sum, which equals $(T-m)r/d$.''

&#x20;   \\item \\textbf{(1)} Cite or briefly justify the $\\Sigma\_\\eta\\to 0^+$ continuity (one line pointing at the LDS model).

&#x20;   \\item \\textbf{(7)} Acknowledge the $c\\lesssim R\_\\cA\\sigma\_\\varepsilon d\_0^{3/2}$ regime switch that lets $c\_0$

&#x20; absorb the clipping.

&#x20;   \\item \\textbf{(8)} Sharpen the remark to ``$d=\\Theta(r)$ with sufficiently large constant'' to avoid the degenerate

&#x20; $d=r$ limit.

&#x20; \\end{enumerate}



&#x20; The core argument is sound. No counterexample found. The $T^{2/3}$ rate holds as stated under the regime $d\\ge d\_0

&#x20; r,T^{1/3}$.





\### GPT response





\[

\\text{Source: }\\mbox{}

]



\[

\\textbf{Claim (1)}\\quad \\text{FLAGGED}

]



\[

\\begin{aligned}

\&\\text{The failing step is ``}\\theta^{(0)}\\equiv 0\\text{ is a valid instance obtained as the limit }\\Sigma\_\\eta\\to 0^+\\text{''.}\\

\&\\text{If the admissible model requires }\\Sigma\_\\eta\\succ 0,\\text{ then for every admissible }\\nu\_0,\\ w\_t=A w\_{t-1}+\\eta\_{t-1}\\text{ is random and }\\theta\_t=B^\\star w\_t\\text{ is not identically }0.\\

\&\\text{Concrete counterexample: }d=r=1,\\ A=0,\\ w\_0=0,\\ \\eta\_0\\sim \\mathcal N(0,\\varepsilon)\\text{ with }\\varepsilon>0;\\ \\theta\_1=\\eta\_0,\\ \\Pr\[\\theta\_1=0]=0,\\text{ so }\\theta\\not\\equiv 0.

\\end{aligned}

]



\[

\\textbf{Claim (2)}\\quad \\text{VERIFIED}

]



\[

\\begin{aligned}

\&\\text{On an exploitation round, }x\_t\\in \\operatorname{range}(\\widehat P\_t)\\text{ and }\\widehat P\_t\\text{ is an orthogonal projector, hence }x\_t=\\widehat P\_t x\_t.\\

\&\\max\_{|x|\\le R\_{\\mathcal A}} x^\\top(\\alpha v)=\\alpha R\_{\\mathcal A}\\text{ at }x=R\_{\\mathcal A}v,\\text{ and }x\_t^\\top v=x\_t^\\top \\widehat P\_t v\\le |x\_t|\*2,|\\widehat P\_t v|\*2\\le R\*{\\mathcal A}|\\widehat P\_t v|\*2.\\

\&\\text{Therefore }\\Delta\_t^{(1)}=R\*{\\mathcal A}\\alpha-\\alpha x\_t^\\top v\\ge R\*{\\mathcal A}\\alpha\\bigl(1-|\\widehat P\_t v|\_2\\bigr);\\text{ this derivation is for exploitation rounds, not probe rounds.}

\\end{aligned}

]



\[

\\textbf{Claim (3)}\\quad \\text{VERIFIED}

]



\[

\\begin{aligned}

\&\\mathrm{KL}(\\mathbb P\_0^{\\mathcal H}|\\mathbb P\_1^{\\mathcal H})

=\\sum\_{t=1}^T \\mathbb E\_{\\mathbb P\_0}!\\left\[\\mathrm{KL}!\\left(\\mathbb P\_0(x\_t,y\_t\\mid \\mathcal H\_{t-1})\\middle|\\mathbb P\_1(x\_t,y\_t\\mid \\mathcal H\_{t-1})\\right)\\right].\\

\&\\text{The }x\_t\\text{-kernel is the same under both instances (deterministic on exploitation rounds, model-independent on probe rounds), so only }y\_t\\mid x\_t\\sim \\mathcal N(x\_t^\\top\\theta^{(i)},\\sigma^2)\\text{ contributes.}\\

\&\\mathrm{KL}!\\left(\\mathcal N(0,\\sigma^2)\\middle|\\mathcal N(\\alpha x\_t^\\top v,\\sigma^2)\\right)=\\frac{\\alpha^2(x\_t^\\top v)^2}{2\\sigma^2},\\text{ so the claimed identity and the }\\mathbb E\_{\\mathbb P\_0}\\text{ expectation are correct.}

\\end{aligned}

]



\[

\\textbf{Claim (4)}\\quad \\text{FLAGGED}

]



\[

\\begin{aligned}

\&\\text{The failing step is ``}\\min\_{|v|=1}\\mathbb E|\\widehat P\_t v|\_2^2\\le r/d\\text{ for each }t,\\ \\text{hence one single }v^\\star\\text{ satisfies }\\sum\_t \\mathbb E|\\widehat P\_t v^\\star|\_2^2\\le (T-m)r/d\\text{''.}\\

\&\\text{Concrete counterexample: }d=2,\\ r=1,\\ \\widehat P\_1=e\_1e\_1^\\top,\\ \\widehat P\_2=e\_2e\_2^\\top;\\ \\min\_v|P\_1v|\*2^2=\\min\_v|P\_2v|\*2^2=0,\\ \\text{but }\\inf\*{|v|=1}\\bigl(|P\_1v|\*2^2+|P\_2v|\*2^2\\bigr)=1.\\

\&\\text{The bound is repairable only by averaging }F(v):=\\mathbb E\*{\\mathbb P\_0}\\sum\*{t\\in\\mathcal T\*{\\mathrm{exp}}}|\\widehat P\_t v|\_2^2\\text{ over uniform }v,\\ \\text{which yields some }v^\\star\\text{ with }F(v^\\star)\\le (T-m)r/d.

\\end{aligned}

]



\[

\\textbf{Claim (5)}\\quad \\text{FLAGGED}

]



\[

\\begin{aligned}

\&\\text{Let }D:=m+R\_{\\mathcal A}^2(T-m)r/d.\\ \\text{With }\\alpha^2=\\sigma^2/(4D),\\text{ one gets }\\mathrm{KL}\\le \\alpha^2D/(2\\sigma^2)=1/8.\\

\&\\text{Using the stated Pinsker inequality }d\_{\\mathrm{TV}}\\le \\sqrt{\\mathrm{KL}/2}\\text{ gives }d\_{\\mathrm{TV}}\\le \\sqrt{(1/8)/2}=1/4.\\

\&\\text{Concrete numerical counterexample: if }\\mathrm{KL}=1/8,\\ \\sqrt{\\mathrm{KL}/2}=1/4\\neq 1/\\sqrt 8;\\text{ the text's }1/\\sqrt 8\\text{ is the wrong constant.}

\\end{aligned}

]



\[

\\textbf{Claim (6)}\\quad \\text{FLAGGED}

]



\[

\\begin{aligned}

\&\\text{The failing step is the per-round inference }\\mathbb E\_{\\nu\_1}|\\widehat P\_t v^\\star|\*2\\le \\sqrt{r/d}+d\*{\\mathrm{TV}}\\text{ from the aggregate control } \\sum\_t \\mathbb E\_{\\nu\_0}|\\widehat P\_t v^\\star|\*2^2\\le (T-m)r/d.\\

\&\\text{Concrete counterexample: }d=2,\\ r=1,\\ \\widehat P\_1=e\_1e\_1^\\top,\\ \\widehat P\_2=e\_2e\_2^\\top,\\ v^\\star=e\_1,\\ d\*{\\mathrm{TV}}=0;\\ \\frac12\\sum\_t|\\widehat P\_t v^\\star|\*2^2=1/2=r/d,\\ \\text{but }|\\widehat P\_1v^\\star|\*2=1>1/\\sqrt2.\\

\&\\text{The regime argument is repairable only after replacing the per-round statement by the averaged bound }\\frac{1}{T-m}\\sum\*{t\\in\\mathcal T\*{\\mathrm{exp}}}\\mathbb E\_{\\nu\_1}|\\widehat P\_t v^\\star|\*2\\le \\sqrt{r/d}+d\*{\\mathrm{TV}},\\text{ which still yields } \\Omega(T^{2/3}).

\\end{aligned}

]



\[

\\textbf{Claim (7)}\\quad \\text{VERIFIED}

]



\[

\\begin{aligned}

\&\\text{For }f(m)=cm+\\beta Tm^{-1/2}\\text{ with }\\beta=c\_1R\_{\\mathcal A}\\sigma,\\ \\ f'(m)=c-\\frac12\\beta T,m^{-3/2}.\\

\&f'(m)=0\\text{ gives }m^\\star=\\left(\\frac{\\beta T}{2c}\\right)^{2/3}=\\Theta!\\left(\\left(\\frac{R\_{\\mathcal A}\\sigma T}{c}\\right)^{2/3}\\right).\\

\&f(m^\\star)=\\Theta!\\bigl(c^{1/3}(\\beta T)^{2/3}\\bigr)=\\Theta!\\bigl(c^{1/3}(R\_{\\mathcal A}\\sigma T)^{2/3}\\bigr),\\text{ so the exponents are correct.}

\\end{aligned}

]



\[

\\textbf{Claim (8)}\\quad \\text{VERIFIED}

]



\[

\\begin{aligned}

\&\\text{If }d=O(r),\\text{ then }R\_{\\mathcal A}^2(T-m)r/d=\\Theta(T),\\text{ so the denominator in }\\alpha^2\\text{ is }m+\\Theta(T)=\\Theta(T)\\text{ whenever }m\\le T.\\

\&\\text{Hence }\\alpha=\\Theta(\\sigma/\\sqrt T),\\text{ and the exploitation term scales as }R\_{\\mathcal A}\\alpha(T-m)=\\Theta(R\_{\\mathcal A}\\sigma \\sqrt T).\\

\&\\text{Thus the large-}d\\text{ }T^{2/3}\\text{ lower-bound mechanism degrades to an }\\Omega(\\sqrt T)\\text{ scale in the small-}d\\text{ regime, exactly as claimed.}

\\end{aligned}

]



\[

\\textbf{Claim (9)}\\quad \\text{VERIFIED}

]



\[

\\begin{aligned}

\&\\text{The key inequality is }|x\_t^\\top v|=|x\_t^\\top \\widehat P\_t v|\\le |x\_t|\_2,|\\widehat P\_t v|\*2\\le R\*{\\mathcal A}|\\widehat P\_t v|\*2,\\text{ and it uses }x\_t=\\widehat P\_t x\_t.\\

\&\\text{Outside }\\Pi\*{\\mathrm{HP}},\\ x\_t^\\top v=x\_t^\\top \\widehat P\_t v+x\_t^\\top(I-\\widehat P\_t)v,\\text{ and the off-subspace term can create additional exploit KL not controlled by the proof.}\\

\&\\text{This class-conditional scope is explicitly stated in the setup and repeated in the final scope remark of the excerpt, so the limitation is clear.}

\\end{aligned}

]







\-------



\#### Chunk\_Cor\_misspec





\### Claude response



&#x20; \\textbf{(1) Perturbation bound $|E\_t|\_\\op \\le 2S\_w\\varepsilon\_k^\\perp + (\\varepsilon\_k^\\perp)^2$.}



&#x20; \\textbf{VERIFIED.} Write $E\_t = T\_1 + T\_1^\\top + T\_2$ with $T\_1 = B\_k^\\star,\\E\[w\_t(\\theta\_t^\\perp)^\\top\\mid\\cH\_{t-1}]$

&#x20;  and $T\_2 = \\E\[\\theta\_t^\\perp(\\theta\_t^\\perp)^\\top\\mid\\cH\_{t-1}]$. Using Jensen on the operator norm (convex) and the

&#x20; rank-1 identity $|uv^\\top|\\op=|u||v|$: $|T\_1|\\op \\le |B\_k^\\star|\\op,\\E\[|w\_t||\\theta\_t^\\perp|] \\le 1\\cdot

&#x20; S\_w\\varepsilon\_k^\\perp$, and $|T\_2|\\op \\le \\E|\\theta\_t^\\perp|^2 \\le (\\varepsilon\_k^\\perp)^2$. Triangle inequality

&#x20; gives $|E\_t|\_\\op \\le 2S\_w\\varepsilon\_k^\\perp + (\\varepsilon\_k^\\perp)^2 \\le 3S\_w\\varepsilon\_k^\\perp$ under

&#x20; $\\varepsilon\_k^\\perp \\le S\_w$.



&#x20; \\textit{Sanity check on symmetry.} $E\_t$ is indeed symmetric: $T\_1+T\_1^\\top$ is manifestly symmetric and $T\_2$ is

&#x20; symmetric, so Davis--Kahan's symmetric-perturbation regime applies.



&#x20; ---

&#x20; \\textbf{(2) $12 = 4\\cdot 3$ in Davis--Kahan under strengthened gap.}



&#x20; \\textbf{VERIFIED.} Under $\\lambda\_{\\min}\\ge 4C\_{\\mathrm{sub}}\\sqrt{\\log(2d/\\delta)/m\_k}+12S\_w\\varepsilon\_k^\\perp$, the

&#x20;  total operator-norm perturbation $|\\widehat M\_k - M\_k^\\star|\\op \\le

&#x20; C{\\mathrm{sub}}\\sqrt{\\log(2d/\\delta)/m\_k}+3S\_w\\varepsilon\_k^\\perp \\le \\lambda\_{\\min}/4$, so by Weyl the effective

&#x20; eigengap satisfies $\\lambda\_r(\\widehat M\_k)-\\lambda\_{r+1}(\\widehat M\_k)\\ge \\lambda\_{\\min}-2|\\text{pert}|\\op\\ge

&#x20; \\lambda{\\min}/2$. The strengthened DK bound $|\\widehat P - P^\\star|\\op \\le 2|\\text{pert}|\\op/\\text{eff.gap} \\le

&#x20; 4|\\text{pert}|\\op/\\lambda{\\min}$ combined with the step-(1) bound yields $4\\cdot

&#x20; 3S\_w\\varepsilon\_k^\\perp/\\lambda\_{\\min} = 12S\_w\\varepsilon\_k^\\perp/\\lambda\_{\\min}$.



&#x20; \\textit{Minor note.} The strengthened gap is roughly $2\\times$ stronger than strictly needed for DK-constant-$4$ to

&#x20; hold (one only needs $|\\text{pert}|\\op\\le\\lambda{\\min}/2$). The paper's slack is conservative but fine; constants

&#x20; match.



&#x20; ---

&#x20; \\textbf{(3) Per-round regret contribution $R\_\\cA(\\varepsilon\_k S\_w + \\varepsilon\_k^\\perp)$.}



&#x20; \\textbf{VERIFIED.} Decompose $(I-\\widehat P\_{t-1})\\theta\_t = (I-\\widehat P\_{t-1})B\_k^\\star w\_t + (I-\\widehat

&#x20; P\_{t-1})\\theta\_t^\\perp$. The equal-rank-projector identity: for unit $v$, $(P\_k^\\star - \\widehat P\_{t-1})B\_k^\\star v =

&#x20;  B\_k^\\star v - \\widehat P\_{t-1}B\_k^\\star v = (I-\\widehat P\_{t-1})B\_k^\\star v$ since $P\_k^\\star B\_k^\\star v = B\_k^\\star

&#x20;  v$. Thus $|(I-\\widehat P\_{t-1})B\_k^\\star|\\op \\le |P\_k^\\star-\\widehat P{t-1}|\\op = \\varepsilon\_k$, giving the first

&#x20; summand $\\le \\varepsilon\_k S\_w$. The second summand $\\le |I-\\widehat P{t-1}|\\op \\varepsilon\_k^\\perp \\le

&#x20; \\varepsilon\_k^\\perp$. Multiply by $R\\cA$. $\\square$



&#x20; ---

&#x20; \\textbf{(4) Final additive factor $(1+S\_w^2/\\lambda\_{\\min})$ --- critical check.}



&#x20; \\textbf{VERIFIED. The $S\_w^2$ is correct; the prior $S\_w$ was genuinely off by a factor of $S\_w$.} Tracing the

&#x20; algebra:

&#x20; \\begin{align\*}

&#x20; R\_\\cA n\_k(\\varepsilon\_k S\_w + \\varepsilon\_k^\\perp)

&#x20; \&\\underset{(\\star)}{\\le} R\_\\cA

&#x20; n\_k!\\left(!\\underbrace{\\tfrac{4C\_{\\mathrm{sub}}\\sqrt{\\log(2d/\\delta)/m\_k}}{\\lambda\_{\\min}}S\_w}{\\text{statistical}}+

&#x20; \\tfrac{12S\_w\\varepsilon\_k^\\perp}{\\lambda{\\min}}\\cdot S\_w + \\varepsilon\_k^\\perp!\\right)\\

&#x20; \&= (\\text{statistical piece}) + R\_\\cA n\_k\\varepsilon\_k^\\perp!\\left(\\tfrac{12 S\_w^2}{\\lambda\_{\\min}} + 1\\right),

&#x20; \\end{align\*}

&#x20; where $(\\star)$ substitutes $\\varepsilon\_k \\le 4C\_{\\mathrm{sub}}\\sqrt{\\log(2d/\\delta)/m\_k}/\\lambda\_{\\min} +

&#x20; 12S\_w\\varepsilon\_k^\\perp/\\lambda\_{\\min}$. The $S\_w^2$ arises unambiguously: \\emph{one} factor of $S\_w$ is already

&#x20; inside $\\varepsilon\_k$ (from the step-(1) bound on the \\emph{matrix-level} perturbation, which has one $|w\_t|$), and

&#x20; \\emph{another} factor of $S\_w$ enters from $|w\_t|$ at the \\emph{vector-level} regret contribution. Replacing either by

&#x20;  "1" or swapping in $S\_w$ alone would drop a $|w\_t|$ from one of these two distinct places.



&#x20; \\textit{Prose nit, not a bug.} The sentence ``when $\\varepsilon\_k^\\perp \\le c\\lambda\_{\\min}/S\_w^2$ the additive term

&#x20; is $O(R\_\\cA\\sum\_k\\varepsilon\_k^\\perp n\_k)$" is loose: the additive term is \\emph{always} linear in

&#x20; $\\varepsilon\_k^\\perp$ with coefficient $(1+12 S\_w^2/\\lambda\_{\\min})$, regardless of regime. The condition

&#x20; $\\varepsilon\_k^\\perp\\le c\\lambda\_{\\min}/S\_w^2$ instead ensures that the \\emph{dimensionless correction}

&#x20; $\\varepsilon\_k^\\perp\\cdot S\_w^2/\\lambda\_{\\min}$ stays $O(1)$, so the DK amplification of the misspec term doesn't blow

&#x20;  up relative to the direct $\\varepsilon\_k^\\perp$ term. Consider rewording.



&#x20; ---

&#x20; \\textbf{(5) Scaled-identity computation $-\\delta\_\\sigma\\mathcal K^{-1}(I\_d) = -\\delta\_\\sigma I\_d/(d+2)$.}



&#x20; \\textbf{VERIFIED.} Plug $N = I\_d$ into $\\mathcal K^{-1}(N) = N/2 - \\tr(N)/(2(d+2))\\cdot I\_d$:

&#x20; $$\\mathcal K^{-1}(I\_d) = \\tfrac{1}{2}I\_d - \\tfrac{d}{2(d+2)}I\_d = \\tfrac{(d+2)-d}{2(d+2)}I\_d = \\tfrac{1}{d+2}I\_d.$$

&#x20; For isotropic Gaussian probes with $\\E\[uu^\\top]=I\_d$, this gives exactly $-\\delta\_\\sigma/(d+2)\\cdot I\_d$. $\\square$



&#x20; ---

&#x20; \\textbf{(6) Sharp bound drops the $\\delta\_\\sigma$ term --- pushing hardest here.}



&#x20; \\textbf{VERIFIED, but the Remark's prose is loose and should be tightened.} The rigorous argument --- which the Remark

&#x20;  gestures at but does not spell out --- is the following \\emph{reference-matrix trick}:



&#x20; Define $\\widetilde M := M\_k^\\star + B\_1$ with $B\_1 := -\\delta\_\\sigma/(d+2)\\cdot I\_d$. Since $B\_1 = cI$ for a scalar

&#x20; $c$, it commutes with every matrix and every orthonormal basis diagonalizes $B\_1$, so

&#x20; $$\\text{top-}r\\text{ eigenspace of }\\widetilde M = \\text{top-}r\\text{ eigenspace of }M\_k^\\star,\\quad P\_{\\widetilde M}

&#x20; = P^\\star,$$

&#x20; \\emph{exactly}, not as a Davis--Kahan consequence. Moreover every eigenvalue of $\\widetilde M$ shifts by $c$, so

&#x20; $\\text{gap}(\\widetilde M) = \\text{gap}(M\_k^\\star) = \\lambda\_{\\min}$. Now apply Davis--Kahan to the pair $(\\widetilde

&#x20; M, \\widehat M\_k)$ instead of $(M\_k^\\star, \\widehat M\_k)$:

&#x20; $$|\\widehat P - P^\\star|\\op = |\\widehat P - P{\\widetilde M}|\\op \\le \\tfrac{c{DK},|\\widehat M\_k - \\widetilde

&#x20; M|\\op}{\\text{gap}(\\widetilde M)} = \\tfrac{c{DK},|B\_2 + \\text{stat.\\ noise}|\\op}{\\lambda{\\min}}.$$

&#x20; The $B\_1$ perturbation \\emph{does not appear} on the right-hand side because we absorbed it into the reference. With

&#x20; $|B\_2|\\op \\le 2L^3\\varepsilon\\times$ and $c\_{DK}=4$ under the strengthened gap, the bias piece contributes $4\\cdot

&#x20; 2L^3\\varepsilon\_\\times/\\lambda\_{\\min} = 8L^3\\varepsilon\_\\times/\\lambda\_{\\min}$, giving $\\Delta\_\\sigma^{\\mathrm{sharp}}

&#x20;  = 8L^3\\varepsilon\_\\times/\\lambda\_{\\min}$. \\checkmark



&#x20; \\textit{Does a scaled identity count as non-rotating"?} Rigorously: yes, but \\emph{not} because Davis--Kahan only

&#x20; responds to eigenvector-rotating perturbations'' (that phrasing is misleading --- DK gives a valid, if loose, bound on

&#x20;  scaled-identity perturbations too). It is because \\emph{the top-$r$ projector is literally the same matrix before and

&#x20;  after adding $cI$}, which means the identity-shift cancels exactly when you pick the right reference. This is an

&#x20; algebraic fact, not a DK property. I recommend rewording the Remark to state the reference-matrix step explicitly ---

&#x20; otherwise a careful reader could push back (as the prompt did).



&#x20; \\textit{Hidden assumptions to verify against the main paper:}

&#x20; \\begin{itemize}\[leftmargin=\*,itemsep=1pt,topsep=1pt]

&#x20; \\item The bias decomposes \\emph{additively} as (scaled-identity $\\delta\_\\sigma$-part) + (operator-norm-bounded

&#x20; $\\varepsilon\_\\times$-part), with no cross-terms where $\\delta\_\\sigma$ multiplies a non-scalar matrix. Under the

&#x20; standard debiasing $\\widehat M\_k = \\mathcal K^{-1}(\\widehat\\E\[y^2 uu^\\top]) - \\hat\\sigma^2\\mathcal

&#x20; K^{-1}(\\widehat\\E\[uu^\\top])$ this holds, since the only $\\hat\\sigma^2$-dependent term is the explicit subtraction.

&#x20; \\item Isotropic'' Gaussian, not merely Gaussian,'' is required: an anisotropic Gaussian with $\\E\[uu^\\top]=\\Sigma\\ne

&#x20; cI$ gives $\\mathcal K^{-1}(\\Sigma)$ which is \\emph{not} a scaled identity and \\emph{does} rotate eigenvectors of

&#x20; $M\_k^\\star$. The Remark correctly says ``isotropic Gaussian.''

&#x20; \\end{itemize}

&#x20; Under these conditions the sharp bound is rigorous.



&#x20; ---

&#x20; \\textbf{(7) Harmonization: $\\Delta\_\\sigma^{\\mathrm{sharp}}\\le \\Delta\_\\sigma$ always.}



&#x20; \\textbf{VERIFIED.}

&#x20; $$\\Delta\_\\sigma - \\Delta\_\\sigma^{\\mathrm{sharp}} = \\tfrac{4|\\delta\_\\sigma|L^2 +

&#x20; 8L^3\\varepsilon\_\\times}{\\lambda\_{\\min}} - \\tfrac{8L^3\\varepsilon\_\\times}{\\lambda\_{\\min}} =

&#x20; \\tfrac{4|\\delta\_\\sigma|L^2}{\\lambda\_{\\min}} \\ge 0. \\quad\\square$$

&#x20; The sharp bound is recovered by setting $\\delta\_\\sigma = 0$ in the conservative one, as expected.



&#x20; ---

&#x20; \\textbf{Summary:} All $7$ claims VERIFIED. No bugs found; two prose-level nits to consider:

&#x20; \\begin{enumerate}\[leftmargin=\*,itemsep=1pt,topsep=1pt]

&#x20; \\item In the Corollary statement, the regime condition when $\\varepsilon\_k^\\perp\\le c\\lambda\_{\\min}/S\_w^2$, the

&#x20; additive term is $O(R\_\\cA\\sum\_k \\varepsilon\_k^\\perp n\_k)$'' is phrased awkwardly --- the linearity in

&#x20; $\\varepsilon\_k^\\perp$ holds unconditionally; the regime condition ensures the $S\_w^2/\\lambda\_{\\min}$ prefactor stays

&#x20; $O(1)$ times $\\varepsilon\_k^\\perp$. \\item In the Remark, saying Davis--Kahan only responds to eigenvector-rotating

&#x20; perturbations'' understates the rigor. The sharper statement is: ``a scalar-identity shift is absorbed into the

&#x20; reference matrix $\\widetilde M := M\_k^\\star - \\delta\_\\sigma/(d+2)\\cdot I\_d$, which has the same top-$r$ projector and

&#x20; the same eigengap as $M\_k^\\star$; Davis--Kahan applied to $(\\widetilde M, \\widehat M\_k)$ then sees only the

&#x20; $\\varepsilon\_\\times$-part of the bias.''

&#x20; \\end{enumerate}

&#x20; Critical factor $S\_w^2$ in (4) is \\emph{correct}; the earlier $S\_w$ version would indeed be off by a factor of $S\_w$.







\### GPT response



\[

\\textbf{Audit of }\\texttt{chunk\_cor\_misspec.tex}

]





\[

\\textbf{(1) PERTURBATION BOUND — VERIFIED}

]

\[

\\begin{aligned}

\&|B\_k^\\star ,\\mathbb E\[w\_t(\\theta\_t^\\perp)^\\top]|\*{\\op}\\le |B\_k^\\star|\*{\\op},\\mathbb E!\\left\[|w\_t(\\theta\_t^\\perp)^\\top|\_{\\op}\\right]

= \\mathbb E\[|w\_t|\*2|\\theta\_t^\\perp|\*2]\\le S\_w,\\epsilon\_k^\\perp,\\

\&|\\mathbb E\[\\theta\_t^\\perp(\\theta\_t^\\perp)^\\top]|\*{\\op}\\le \\mathbb E!\\left\[|\\theta\_t^\\perp(\\theta\_t^\\perp)^\\top|\*{\\op}\\right]

= \\mathbb E|\\theta\_t^\\perp|\*2^2\\le (\\epsilon\_k^\\perp)^2,\\

\&\\text{hence }|E\_t|\*{\\op}\\le 2S\_w\\epsilon\_k^\\perp+(\\epsilon\_k^\\perp)^2\\le 3S\_w\\epsilon\_k^\\perp\\ \\text{when }\\epsilon\_k^\\perp\\le S\_w;\\ \\text{the constant }3\\text{ is valid but generally loose.}

\\end{aligned}

]



\[

\\textbf{(2) DAVIS\\text{--}KAHAN WITH STRENGTHENED EIGENGAP — VERIFIED}

]

\[

\\begin{aligned}

\&\\text{Let }\\eta\_k:=C\_{\\mathrm{sub}}\\sqrt{\\log(2d/\\delta)/m\_k}+3S\_w\\epsilon\_k^\\perp,\\ \\text{so the total perturbation from }A\_k:=B\_k^\\star\\bar S\_k(B\_k^\\star)^\\top\\text{ is }|\\widehat M\_k-A\_k|\*{\\op}\\le \\eta\_k,\\

\&\\lambda\_r(A\_k)=\\lambda\*{\\min},\\ \\lambda\_{r+1}(A\_k)=0,\\ \\text{and for rank-}r\\text{ PSD }A\_k\\text{ one has }|\\widehat P\_k-P\_k^\\star|\*{\\op}\\le \\frac{2\\eta\_k}{\\lambda\*{\\min}-\\eta\_k}\\le \\frac{4\\eta\_k}{\\lambda\_{\\min}}\\ \\text{whenever }\\eta\_k\\le \\lambda\_{\\min}/2,\\

\&\\lambda\_{\\min}\\ge 4\\eta\_k\\ \\text{is stronger than needed and implies }\\varepsilon\_k\\le \\frac{4C\_{\\mathrm{sub}}\\sqrt{\\log(2d/\\delta)/m\_k}}{\\lambda\_{\\min}}+\\frac{12S\_w\\epsilon\_k^\\perp}{\\lambda\_{\\min}};\\ \\text{the }12=4\\cdot 3\\text{ is correct.}

\\end{aligned}

]



\[

\\textbf{(3) REGRET CONTRIBUTION — VERIFIED}

]

\[

\\begin{aligned}

\&|x\_t^\\top(I-\\widehat P\_{t-1})\\theta\_t|\\le |x\_t|\*2,|(I-\\widehat P\*{t-1})\\theta\_t|\*2

\\le R\*{\\mathcal A}!\\left(|(I-\\widehat P\_{t-1})B\_k^\\star w\_t|\*2+|(I-\\widehat P\*{t-1})\\theta\_t^\\perp|\*2\\right),\\

\&(I-\\widehat P\*{t-1})B\_k^\\star=(P\_k^\\star-\\widehat P\_{t-1})B\_k^\\star,\\ \\text{so }|(I-\\widehat P\_{t-1})B\_k^\\star w\_t|\*2\\le |P\_k^\\star-\\widehat P\*{t-1}|\*{\\op}|w\_t|\*2\\le \\varepsilon\_k S\_w,\\

\&|(I-\\widehat P\*{t-1})\\theta\_t^\\perp|\*2\\le |I-\\widehat P\*{t-1}|\*{\\op}|\\theta\_t^\\perp|\*2\\le \\epsilon\_k^\\perp,\\ \\text{hence the per-round contribution is }R\*{\\mathcal A}(\\varepsilon\_k S\_w+\\epsilon\_k^\\perp).

\\end{aligned}

]



\[

\\textbf{(4) FINAL ADDITIVE TERM — VERIFIED}

]

\[

\\begin{aligned}

\&R\_{\\mathcal A}n\_k(\\varepsilon\_k S\_w+\\epsilon\_k^\\perp)\\le R\_{\\mathcal A}n\_k!\\left\[S\_w!\\left(\\frac{4C\_{\\mathrm{sub}}\\sqrt{\\log(2d/\\delta)/m\_k}}{\\lambda\_{\\min}}+\\frac{12S\_w\\epsilon\_k^\\perp}{\\lambda\_{\\min}}\\right)+\\epsilon\_k^\\perp\\right],\\

\&= (\\text{statistical term})+R\_{\\mathcal A}n\_k,\\epsilon\_k^\\perp!\\left(1+\\frac{12S\_w^2}{\\lambda\_{\\min}}\\right),\\

\&\\text{so the corollary’s }O!\\bigl(R\_{\\mathcal A}\\sum\_k \\epsilon\_k^\\perp(1+S\_w^2/\\lambda\_{\\min})n\_k\\bigr)\\text{ is the right scaling; replacing }S\_w^2/\\lambda\_{\\min}\\text{ by }S\_w/\\lambda\_{\\min}\\text{ is off by one factor of }S\_w.

\\end{aligned}

]



\[

\\textbf{(5) VARIANCE-MISSPEC REMARK: SCALED IDENTITY CLAIM — VERIFIED}

]

\[

\\begin{aligned}

\&\\mathcal K^{-1}(I\_d)=\\frac{1}{2}I\_d-\\frac{\\operatorname{tr}(I\_d)}{2(d+2)}I\_d=\\frac{1}{2}I\_d-\\frac{d}{2(d+2)}I\_d,\\

\&\\frac{1}{2}-\\frac{d}{2(d+2)}=\\frac{d+2-d}{2(d+2)}=\\frac{1}{d+2},\\ \\text{so }\\mathcal K^{-1}(I\_d)=\\frac{1}{d+2}I\_d,\\

\&-\\delta\_\\sigma,\\mathcal K^{-1}(\\mathbb E\[uu^\\top])=-\\delta\_\\sigma,\\mathcal K^{-1}(I\_d)=-\\frac{\\delta\_\\sigma}{d+2}I\_d.

\\end{aligned}

]



\[

\\textbf{(6) VARIANCE-MISSPEC REMARK: CONSERVATIVE vs SHARP BOUND — VERIFIED}

]

\[

\\begin{aligned}

\&\\text{Write }\\widehat M\_k=A\_k+cI\_d+B\_k+N\_k,\\qquad c:=-\\delta\_\\sigma/(d+2),\\qquad |B\_k|\*{\\op}\\le 2L^3\\epsilon\*\\times,\\

\&\\text{for every matrix }M,\\ M\\text{ and }M-cI\_d\\text{ have exactly the same eigenvectors and the same eigengap }(\\lambda\_r-\\lambda\_{r+1}),\\ \\text{so the }cI\_d\\text{ term cannot rotate the top-}r\\text{ subspace},\\

\&\\text{therefore Davis--Kahan may be applied after removing }cI\_d,\\ \\text{and only }2L^3\\epsilon\_\\times\\text{ contributes to bias, giving }\\Delta\_\\sigma^{\\mathrm{sharp}}=\\frac{4\\cdot 2L^3\\epsilon\_\\times}{\\lambda\_{\\min}}=\\frac{8L^3\\epsilon\_\\times}{\\lambda\_{\\min}}.

\\end{aligned}

]



\[

\\textbf{(7) HARMONIZATION — VERIFIED}

]

\[

\\begin{aligned}

\&\\Delta\_\\sigma=\\frac{4(|\\delta\_\\sigma|L^2+2L^3\\epsilon\_\\times)}{\\lambda\_{\\min}}

=\\frac{4|\\delta\_\\sigma|L^2}{\\lambda\_{\\min}}+\\frac{8L^3\\epsilon\_\\times}{\\lambda\_{\\min}}\\ge \\frac{8L^3\\epsilon\_\\times}{\\lambda\_{\\min}}=\\Delta\_\\sigma^{\\mathrm{sharp}},\\

\&\\text{so the theorem’s }\\Delta\_\\sigma\\text{ is a conservative all-probe bound, while the remark gives a strictly sharper specialization under the extra assumption of isotropic Gaussian probes},\\

\&\\text{these statements are consistent rather than contradictory; the only editorial improvement would be one explicit sentence saying that the remark specializes Theorem }1\\text{ under stronger assumptions.}

\\end{aligned}

]





\------



\#### Chunk\_truncation





\### Claude response



\\textbf{Adversarial review of \\texttt{chunk\_truncation.tex}.}



&#x20; I re-derived each claim from scratch before accepting it. Summary: $8$ of $9$ items pass; step $(5c)$ contains an

&#x20; algebraic error (off by $4$ powers of $S\_w, \\sigma, \\hat\\sigma$) that I can exhibit with a concrete counterexample,

&#x20; though the final $O(d^2)$ conclusion survives.



&#x20; \\vspace{0.5em}

&#x20; \\textbf{(1) Chi-squared tail: $L^2 = 2d\\log(4T/\\delta) ;\\Rightarrow; \\Pr(|u|>L) \\le \\delta/(4T)$.}\\

&#x20; \\textbf{VERIFIED}, but with a subtle slackness the proof papers over. Laurent--Massart states $\\Pr(|u|^2 \\ge d +

&#x20; 2\\sqrt{dx} + 2x) \\le e^{-x}$ with $x = \\log(4T/\\delta)$. For the subset ${|u|^2 > 2dx} \\subseteq {|u|^2 > d +

&#x20; 2\\sqrt{dx} + 2x}$, we need $2dx \\ge d + 2\\sqrt{dx} + 2x$. AM-GM gives $d + 2\\sqrt{dx} + 2x \\le 2d + 3x$, so it

&#x20; suffices to check $2dx \\ge 2d + 3x$, i.e.\\ $x \\ge 2d/(2d-3)$. This holds for $d \\ge 2, x \\ge 4$ (i.e.\\ $T/\\delta \\ge

&#x20; e^4/4 \\approx 14$), trivially for $d \\ge 3, x \\ge 2$. For $d = 1$ the inequality $2x \\ge 1 + 2\\sqrt{x} + 2x$ literally

&#x20;  fails, but the bound still holds via the direct Gaussian tail $\\Pr(|Z| > \\sqrt{2x}) \\le e^{-x}$. Conclusion: the

&#x20; claim is correct, but the citation ``Laurent--Massart'' is technically incomplete at $d=1$ and tight at $d=2$. For the

&#x20;  typical bandit regime ($d \\ge 2, T \\gg 1$) this is fine.



&#x20; \\vspace{0.3em}

&#x20; \\textbf{(2) Sub-Gaussian tail: $L\_\\varepsilon = \\sigma\\sqrt{2\\log(4T/\\delta)}$.}\\

&#x20; \\textbf{VERIFIED.} For $\\varepsilon \\sim \\mathcal{N}(0, \\sigma^2)$, $\\Pr(|\\varepsilon| > t) \\le 2

&#x20; e^{-t^2/(2\\sigma^2)}$. Plug $t = L\_\\varepsilon$: $L\_\\varepsilon^2/(2\\sigma^2) = \\log(4T/\\delta)$, so

&#x20; $\\Pr(|\\varepsilon| > L\_\\varepsilon) \\le 2 e^{-\\log(4T/\\delta)} = \\delta/(2T)$. $\\checkmark$



&#x20; \\vspace{0.3em}

&#x20; \\textbf{(3) Subset relation: ${|y|>L\_y} \\cap {|u|\\le L} \\subseteq {|\\varepsilon|>L\_\\varepsilon}$.}\\

&#x20; \\textbf{VERIFIED CONDITIONALLY.} From $\\varepsilon = y - u^\\top\\theta$ and $|\\theta| \\le S\_w$: $|\\varepsilon| \\ge |y|

&#x20; - |u||\\theta| \\ge L\_y - LS\_w$ on the intersection. This implies $|\\varepsilon| > L\_\\varepsilon$ \\emph{iff} $L\_y \\ge

&#x20; L\_\\varepsilon + LS\_w$. The chunk does not define $L\_y$ --- it defers to ``Lemma G\_bound'' --- so the subset relation

&#x20; is correct provided that external lemma sets $L\_y \\ge L\_\\varepsilon + LS\_w$. \\textbf{Action:} verify \\texttt{Lemma

&#x20; G\_bound} uses this threshold; otherwise the probability accounting collapses.



&#x20; \\vspace{0.3em}

&#x20; \\textbf{(4) Union bound arithmetic.}\\

&#x20; \\textbf{VERIFIED.} Decomposition: $\\mathcal{A}t^c = {|u|>L} \\cup ({|y|>L\_y} \\cap {|u|\\le L}) \\subseteq {|u|>L} \\cup

&#x20; {|\\varepsilon|>L\\varepsilon}$. Hence $\\Pr(\\mathcal{A}\_t^c) \\le \\delta/(4T) + \\delta/(2T) = 3\\delta/(4T) \\le \\delta/T$.

&#x20;  $\\checkmark$



&#x20; \\vspace{0.3em}

&#x20; \\textbf{(5) Moment bound $\\mathbb{E}\[|G\_t|{\\mathrm{op}}^2\\mid\\mathcal{H}{t-1}] = O(d^2)$.}



&#x20; \\textbf{(5a) $|G\_t|{\\mathrm{op}} \\le |s\_t||u|^2$.} \\textbf{VERIFIED (conditionally).} Submultiplicativity:

&#x20; $|\\mathcal{K}^{-1}(s\_t uu^\\top)|{\\mathrm{op}} \\le |\\mathcal{K}^{-1}|{\\mathrm{op}\\to\\mathrm{op}} \\cdot

&#x20; |s\_t||uu^\\top|{\\mathrm{op}} = |\\mathcal{K}^{-1}|{\\mathrm{op}\\to\\mathrm{op}}\\cdot|s\_t||u|^2$. The bound

&#x20; $|\\mathcal{K}^{-1}|{\\mathrm{op}\\to\\mathrm{op}} \\le 1$ must be proven elsewhere (it is a property of the specific

&#x20; Gaussian superoperator); I accept it on faith here.



&#x20; \\textbf{(5b) $|s\_t| \\le 2(u^\\top\\theta)^2 + 2\\varepsilon^2 + \\hat\\sigma^2$.} \\textbf{VERIFIED.} Assuming $s\_t = y^2 -

&#x20; \\hat\\sigma^2$ (or any $|s\_t| \\le y^2 + \\hat\\sigma^2$), use $y^2 \\le 2(u^\\top\\theta)^2 + 2\\varepsilon^2$. $\\checkmark$



&#x20; \\textbf{(5c) $\\mathbb{E}\[s\_t^4\\mid\\mathcal{H}\_{t-1}] \\le C(S\_w^4 + \\sigma^4 + \\hat\\sigma^4)$.} \\textbf{FLAGGED.}\\

&#x20; The author's ``key'' hint reads: \\emph{$(u^\\top\\theta)^4$ has 4th moment $3|\\theta|^4 \\le 3S\_w^4$.} But

&#x20; $\\mathbb{E}\[(u^\\top\\theta)^4] = 3|\\theta|^4$ is what you need to bound $\\mathbb{E}\[s\_t^2]$, not $\\mathbb{E}\[s\_t^4]$.

&#x20; Correct derivation:

&#x20; \[

&#x20; s\_t^4 \\le \\bigl(2(u^\\top\\theta)^2 + 2\\varepsilon^2 + \\hat\\sigma^2\\bigr)^4 \\le 27 \\bigl(16(u^\\top\\theta)^8 +

&#x20; 16\\varepsilon^8 + \\hat\\sigma^8\\bigr).

&#x20; ]

&#x20; Since $u^\\top\\theta \\sim \\mathcal{N}(0,|\\theta|^2)$, $\\mathbb{E}\[(u^\\top\\theta)^8] = 7!!,|\\theta|^8 = 105|\\theta|^8$,

&#x20; giving

&#x20; \[

&#x20; \\mathbb{E}\[s\_t^4] \\le C\\bigl(S\_w^8 + \\sigma^8 + \\hat\\sigma^8\\bigr), \\quad \\text{NOT } C(S\_w^4 + \\sigma^4 +

&#x20; \\hat\\sigma^4).

&#x20; ]

&#x20; \\textbf{Concrete counterexample.} Take $d = 1$, $\\theta = S\_w$, $\\sigma = \\hat\\sigma = 0$. Then $s\_t = y^2 = S\_w^2

&#x20; u^2$, so

&#x20; \[

&#x20; \\mathbb{E}\[s\_t^4] = S\_w^8,\\mathbb{E}\[u^8] = 105,S\_w^8.

&#x20; ]

&#x20; This is $\\Theta(S\_w^8)$ and exceeds any fixed $C\\cdot S\_w^4$ whenever $S\_w > \\sqrt\[4]{C/105}$. So the stated bound

&#x20; \\emph{fails} for all large $S\_w$.\\

&#x20; \\textbf{Root cause:} the author confused $\\mathbb{E}\[s\_t^2]$ (which does equal $O(S\_w^4 + \\sigma^4 + \\hat\\sigma^4)$

&#x20; via $\\mathbb{E}\[(u^\\top\\theta)^4]=3|\\theta|^4$) with $\\mathbb{E}\[s\_t^4]$. Step (5e) explicitly requires

&#x20; $\\mathbb{E}\[s\_t^4]$, so the wrong moment is cited.\\

&#x20; \\textbf{Downstream impact:} the error is \\emph{cosmetic} --- $S\_w^8$ is still constant in $d$. The $O(d^2)$ conclusion

&#x20;  of (5) still holds with worse constants. But the proof must be rewritten to replace $S\_w^4 \\to S\_w^8$, $\\sigma^4 \\to

&#x20; \\sigma^8$, $\\hat\\sigma^4 \\to \\hat\\sigma^8$.



&#x20; \\textbf{(5d) $\\mathbb{E}\[|u|^8] = d(d+2)(d+4)(d+6)$.} \\textbf{VERIFIED.} $\\chi^2\_d$ has $k$-th moment

&#x20; $\\prod\_{j=0}^{k-1}(d+2j)$; here $k=4$. $\\checkmark$



&#x20; \\textbf{(5e) Cauchy--Schwarz step.} \\textbf{VERIFIED.} $\\mathbb{E}\[s\_t^2|u|^4] \\le

&#x20; \\sqrt{\\mathbb{E}\[s\_t^4],\\mathbb{E}\[|u|^8]} \\le \\sqrt{O(1)\\cdot O(d^4)} = O(d^2)$. See (6) below for the

&#x20; no-independence argument.



&#x20; \\vspace{0.3em}

&#x20; \\textbf{(6) Cauchy--Schwarz without independence.}\\

&#x20; \\textbf{VERIFIED.} For any two random variables $X, Y \\in L^2(\\Omega, \\mathcal{F}, \\mathbb{P})$, the inequality

&#x20; $|\\mathbb{E}\[XY]| \\le \\sqrt{\\mathbb{E}\[X^2],\\mathbb{E}\[Y^2]}$ is a purely algebraic consequence of $\\langle X,

&#x20; Y\\rangle\_{L^2} \\le |X|{L^2}|Y|{L^2}$. \\textbf{No independence is ever invoked.} With $X = s\_t^2, Y = |u|^4$ (both

&#x20; $\\mathcal{F}t$-measurable, neither independent of the other since $s\_t$ depends on $u\_t$), the inequality holds

&#x20; unconditionally. Also holds conditionally on $\\mathcal{H}{t-1}$ via the same argument applied on $(\\Omega,

&#x20; \\mathcal{F}, \\mathbb{P}(\\cdot\\mid\\mathcal{H}\_{t-1}))$. $\\checkmark$



&#x20; \\vspace{0.3em}

&#x20; \\textbf{(7) $\\Theta$ bound.}\\

&#x20; \\textbf{VERIFIED.} Two-step chain:

&#x20; \[

&#x20; \\bigl|\\mathbb{E}\[G\_t\\mathbf{1}{\\mathcal{A}t^c}\\mid\\mathcal{H}{t-1}]\\bigr|{\\mathrm{op}}

&#x20; \\stackrel{()}{\\le} \\mathbb{E}\[|G\_t|{\\mathrm{op}}\\mathbf{1}{\\mathcal{A}t^c}\\mid\\mathcal{H}{t-1}]

&#x20; \\stackrel{(\*\*)}{\\le}

&#x20; \\sqrt{\\mathbb{E}\[|G\_t|{\\mathrm{op}}^2\\mid\\mathcal{H}{t-1}]}\\cdot\\sqrt{\\Pr(\\mathcal{A}t^c\\mid\\mathcal{H}{t-1})}.

&#x20; ]

&#x20; Here $()$ is Jensen applied to the convex map $M \\mapsto |M|{\\mathrm{op}}$; $(\*\*)$ is Cauchy--Schwarz with $X =

&#x20; |G\_t|{\\mathrm{op}}$, $Y = \\mathbf{1}\_{\\mathcal{A}\_t^c}$ (so $\\mathbb{E}\[Y^2] = \\Pr(\\mathcal{A}t^c)$). Plugging

&#x20; $O(d^2)\\cdot\\delta/T$ gives per-round $O(d\\sqrt{\\delta/T})$, and averaging $m\_k$ per-round bounds (all the same)

&#x20; yields $|\\Theta\_k|{\\mathrm{op}} \\le O(d\\sqrt{\\delta/T})$. $\\checkmark$



&#x20; \\vspace{0.3em}

&#x20; \\textbf{(8) Dominance.}\\

&#x20; \\textbf{VERIFIED} --- robustly, in fact. With $m\_k = T^{2/3}$ and Freedman rate $O(R\_X\\sqrt{\\log(T)/m\_k})$:

&#x20; \\begin{itemize}

&#x20; \\item If $R\_X = O(d^2 \\log^2 T)$ (the user's prompt): Freedman rate $= O(d^2 \\log^{5/2}(T) / T^{1/3})$.

&#x20; \\item If $R\_X = O(d \\log^2 T)$ (the chunk's line 88): Freedman rate $= O(d \\log^{5/2}(T) / T^{1/3})$.

&#x20; \\end{itemize}

&#x20; $\\Theta\_k = O(d/\\sqrt{T})$ (taking $\\delta = 1/\\mathrm{poly}(T)$). Ratio $\\Theta\_k / \\mathrm{Freedman}$:

&#x20; \[

&#x20; \\frac{d/\\sqrt{T}}{d^\\alpha \\log^{5/2}(T)/T^{1/3}} = \\frac{1}{d^{\\alpha-1} T^{1/6} \\log^{5/2}(T)} \\to 0, \\quad

&#x20; \\alpha\\in{1,2}.

&#x20; ]

&#x20; Dominance holds in either case. \\emph{Note}: there is an internal inconsistency --- the chunk line 88 says $R\_X =

&#x20; O(d\\log^2 T)$ while the user's prompt says $O(d^2\\log^2 T)$. Worth reconciling for the final write-up. If $R\_s \\sim

&#x20; L\_y^2 = O(L\_\\varepsilon^2 + L^2 S\_w^2) = O(d\\log T)$, then $L^2 R\_s = O(d^2 \\log^2 T)$, favoring the user's prompt.

&#x20; $\\checkmark$



&#x20; \\vspace{0.3em}

&#x20; \\textbf{(9) Unconditional vs.\\ conditional formulation --- is the current version bug-free?}\\

&#x20; \\textbf{VERIFIED, and the formulation cleanly escapes both prior bugs.}\\

&#x20; The decomposition is:

&#x20; \[

&#x20; \\frac{1}{m\_k}\\sum\_{t\\in\\mathcal{T}k} G\_t ;=; \\frac{1}{m\_k}\\sum\_t \\tilde{X}t ;+; \\frac{1}{m\_k}\\sum\_t \\mathbb{E}\[\\tilde

&#x20; G\_t\\mid\\mathcal{H}{t-1}] ;+; \\frac{1}{m\_k}\\sum\_t G\_t\\mathbf{1}{\\mathcal{A}t^c},

&#x20; ]

&#x20; where $\\tilde G\_t = G\_t \\mathbf{1}{\\mathcal{A}t}$ and $\\tilde X\_t = \\tilde G\_t - \\mathbb{E}\[\\tilde

&#x20; G\_t\\mid\\mathcal{H}{t-1}]$ is an MDS. Using $\\mathbb{E}\[\\tilde G\_t\\mid\\mathcal{H}] = \\mathbb{E}\[G\_t\\mid\\mathcal{H}] -

&#x20; \\mathbb{E}\[G\_t\\mathbf{1}\_{\\mathcal{A}\_t^c}\\mid\\mathcal{H}]$, the target $\\mathbb{E}\[G\_t\\mid\\mathcal{H}] = \\Sigma$ is

&#x20; recovered modulo the bias $\\Theta\_k$. On the high-probability event $\\bigcap\_t \\mathcal{A}t$ (prob $\\ge 1-\\delta$),

&#x20; the random tail $\\sum\_t G\_t\\mathbf{1}{\\mathcal{A}\_t^c}$ vanishes exactly, leaving only the deterministic $\\Theta\_k$

&#x20; plus Freedman. This avoids the two prior bugs: \\textbf{(i)} $G\_t$ is defined via the correct \\emph{untruncated}

&#x20; operator $\\mathcal{K}^{-1}$, so no ``wrong conditional operator'' enters; \\textbf{(ii)} $\\mathcal{A}\_t$ enforces

&#x20; \\emph{both} $|u|\\le L$ \\emph{and} $|y|\\le L\_y$ (the latter disciplining $\\varepsilon$ via the subset relation), so

&#x20; Freedman's a.s.\\ boundedness hypothesis is genuinely met. $\\checkmark$



&#x20; \\vspace{0.5em}

&#x20; \\textbf{Verdict.}

&#x20; \\begin{itemize}

&#x20; \\item\[$\\checkmark$] Overall logical structure is sound. The new $\\mathcal{A}t$-based formulation correctly separates

&#x20; the bias and martingale parts.

&#x20; \\item\[$!$] \\textbf{One real error}: (5c) states $\\mathbb{E}\[s\_t^4] \\le C(S\_w^4 + \\sigma^4 + \\hat\\sigma^4)$; correct is

&#x20;  $\\mathbb{E}\[s\_t^4] \\le C(S\_w^8 + \\sigma^8 + \\hat\\sigma^8)$. Fix by relabeling powers throughout the paragraph. Does

&#x20; \\emph{not} affect the $O(d^2)$ conclusion.

&#x20; \\item\[$?$] \\textbf{Two external dependencies} to verify outside this chunk: (a) $L\_y = L\\varepsilon + LS\_w$ in Lemma

&#x20; G\_bound (for (3)); (b) $|\\mathcal{K}^{-1}|\_{\\mathrm{op}\\to\\mathrm{op}}\\le 1$ (for (5a)). Both are standard but not

&#x20; proven here.

&#x20; \\item\[$?$] \\textbf{Internal inconsistency} on $R\_X$ (line 88 vs.\\ prompt's $O(d^2\\log^2 T)$). Dominance holds either

&#x20; way; worth reconciling for polish.

&#x20; \\item\[$\\sim$] \\textbf{Minor}: (1) is correct but the Laurent--Massart citation is tight to the point of edge-case

&#x20; failure at $d=2, x<4$; robust for bandit regime.

&#x20; \\end{itemize}



&#x20; \\textbf{Recommendation:} fix the $S\_w^4 \\to S\_w^8$ typo in (5c) and cross-check the two external dependencies. The

&#x20; proof is then bug-free.







\### GPT response





\[

\\begin{aligned}

\&\\text{\\textbf{(1) FLAGGED}}\\

\&\\text{The Laurent--Massart deduction needs }d+2\\sqrt{dx}+2x \\le L^2=2dx,\\quad x:=\\log(4T/\\delta).\\

\&\\text{This fails in general: }d=2,\\ x=2\\text{ gives }d+2\\sqrt{dx}+2x=10>8=2dx.\\

\&\\text{So the proof step is invalid as written; the factor }4\\text{ does give }e^{-x}=\\delta/(4T),\\text{ but an extra threshold comparison is still needed.}

\\end{aligned}

]





\[

\\begin{aligned}

\&\\text{\\textbf{(2) VERIFIED}}\\

\&\\text{For a }\\sigma\_\\varepsilon\\text{-sub-Gaussian scalar, }\\Pr(|\\varepsilon|>t)\\le 2\\exp!\\bigl(-t^2/(2\\sigma\_\\varepsilon^2)\\bigr).\\

\&\\text{At }t=L\_\\varepsilon=\\sigma\_\\varepsilon\\sqrt{2\\log(4T/\\delta)},\\ \\exp!\\bigl(-L\_\\varepsilon^2/(2\\sigma\_\\varepsilon^2)\\bigr)=e^{-\\log(4T/\\delta)}.\\

\&\\text{Hence }\\Pr(|\\varepsilon|>L\_\\varepsilon)\\le 2e^{-\\log(4T/\\delta)}=2\\cdot \\frac{\\delta}{4T}=\\frac{\\delta}{2T}.

\\end{aligned}

]





\[

\\begin{aligned}

\&\\text{\\textbf{(3) VERIFIED}}\\

\&\\text{On }{|u\_t|\\le L},\\ \\ |u\_t^\\top\\theta\_t|\\le |u\_t|,|\\theta\_t|\\le LS\_w.\\

\&\\text{Therefore }|y\_t|=|u\_t^\\top\\theta\_t+\\varepsilon\_t|\\le LS\_w+|\\varepsilon\_t|.\\

\&\\text{So }|y\_t|>L\_y=LS\_w+L\_\\varepsilon\\text{ and }|u\_t|\\le L\\text{ together force }|\\varepsilon\_t|>L\_\\varepsilon.

\\end{aligned}

]





\[

\\begin{aligned}

\&\\text{\\textbf{(4) VERIFIED}}\\

\&\\text{If }\\omega\\in \\mathcal A\_t^c={|u\_t|>L}\\cup{|y\_t|>L\_y},\\text{ then either }|u\_t|>L\\text{ already, or }|y\_t|>L\_y.\\

\&\\text{In the second case, either }|u\_t|>L\\text{ or }|u\_t|\\le L,\\text{ and then Claim (3) gives }|\\varepsilon\_t|>L\_\\varepsilon.\\

\&\\text{Thus }\\mathcal A\_t^c\\subseteq{|u\_t|>L}\\cup{|\\varepsilon\_t|>L\_\\varepsilon},\\text{ and } \\frac{\\delta}{4T}+\\frac{\\delta}{2T}=\\frac{3\\delta}{4T}\\le \\frac{\\delta}{T}.

\\end{aligned}

]





\[

\\begin{aligned}

\&\\text{\\textbf{(5) FLAGGED}}\\

\&\\text{The failing step is (c): }\\E\[s\_t^4\\mid\\mathcal H\_{t-1}] \\le C(S\_w^4+\\sigma\_\\varepsilon^4+\\hat\\sigma^4)\\text{ is false as written.}\\

\&\\text{Counterexample: }\\varepsilon\_t\\equiv 0,\\ \\hat\\sigma=0,\\ |\\theta\_t|=M\\ \\Rightarrow\\ s\_t=(u\_t^\\top\\theta\_t)^2,\\ \\E\[s\_t^4]=\\E\[(u\_t^\\top\\theta\_t)^8]=105M^8.\\

\&\\text{This cannot be bounded by }CM^4\\text{ uniformly; the correct parameter scaling is }C(S\_w^8+\\sigma\_\\varepsilon^8+\\hat\\sigma^8),\\text{ which still yields }O(d^2).

\\end{aligned}

]

&#x20;



\[

\\begin{aligned}

\&\\text{\\textbf{(6) VERIFIED}}\\

\&\\text{Take }X:=|s\_t|^2,\\quad Y:=|u\_t|^4,\\text{ so that }\\E\[s\_t^2|u\_t|^4\\mid\\mathcal H\_{t-1}]=\\E\[XY\\mid\\mathcal H\_{t-1}].\\

\&\\text{Conditional Cauchy--Schwarz gives }\\E\[XY\\mid\\mathcal H\_{t-1}] \\le \\sqrt{\\E\[X^2\\mid\\mathcal H\_{t-1}],\\E\[Y^2\\mid\\mathcal H\_{t-1}]}.\\

\&\\text{Hence }\\E\[s\_t^2|u\_t|^4\\mid\\mathcal H\_{t-1}] \\le \\sqrt{\\E\[s\_t^4\\mid\\mathcal H\_{t-1}],\\E\[|u\_t|^8]},\\text{ with no independence assumption anywhere.}

\\end{aligned}

]





\[

\\begin{aligned}

\&\\text{\\textbf{(7) VERIFIED}}\\

\&\\text{For any random matrix }M\\text{ and event }A,\\ |\\E\[M\\mathbf 1\_A\\mid\\mathcal H]|\*{\\op}\\le \\E\[|M|\*{\\op}\\mathbf 1\_A\\mid\\mathcal H]\\le \\sqrt{\\E\[|M|\*{\\op}^2\\mid\\mathcal H]\\Pr(A\\mid\\mathcal H)}.\\

\&\\text{Applying this with }M=G\_t,\\ A=\\mathcal A\_t^c,\\ \\E\[|G\_t|\*{\\op}^2\\mid\\mathcal H\_{t-1}]=O(d^2),\\ \\Pr(\\mathcal A\_t^c\\mid\\mathcal H\_{t-1})\\le \\delta/T\\text{ gives }O(d\\sqrt{\\delta/T}).\\

\&\\text{Then }|\\Theta\_k|\*{\\op}\\le m\_k^{-1}\\sum\*{t\\in\\mathcal T\_k} O(d\\sqrt{\\delta/T})=O(d\\sqrt{\\delta/T}).

\\end{aligned}

]





\[

\\begin{aligned}

\&\\text{\\textbf{(8) VERIFIED}}\\

\&\\text{With }L^2=O(d\\log T)\\text{ and }L\_y^2=O((LS\_w+L\_\\varepsilon)^2)=O(d\\log T),\\text{ one gets }R\_s=O(d\\log T)\\text{ and }R\_X=L^2R\_s+S\_w^2=O(d^2\\log^2 T).\\

\&\\text{So the Freedman term is }O!\\bigl(d^2\\log^{5/2}(T)/\\sqrt{m\_k}\\bigr)=O(d^2/T^{1/3})\\text{ when }m\_k=O(T^{2/3})\\text{, up to polylogs.}\\

\&\\text{Since }d/\\sqrt T \\le d^2/T^{1/3}\\iff 1\\le dT^{1/6},\\text{ the bias is dominated for all }d,T\\ge 1;\\text{ only the appendix's displayed }O(d\\log^2T)\\text{ is dimensionally off.}

\\end{aligned}

]





\[

\\begin{aligned}

\&\\text{\\textbf{(9) VERIFIED}}\\

\&\\text{Here }G\_t=\\mathcal K^{-1}(s\_tu\_tu\_t^\\top)\\text{ is defined under the original Gaussian law, so no conditional truncated operator }\\mathcal K\_L\\text{ and no missing normalization ever appear.}\\

\&\\text{The truncation enters only through }\\tilde G\_t=G\_t\\mathbf 1{\\mathcal A\_t},\\text{ and the discarded mass is tracked exactly by }\\Theta\_k=m\_k^{-1}\\sum\_t \\E\[G\_t\\mathbf 1{\\mathcal A\_t^c}\\mid\\mathcal H\_{t-1}].\\

\&\\text{Using both }|u\_t|\\text{- and }|y\_t|\\text{-truncation makes the increment bound observable and removes the earlier bug caused by leaving the noise term effectively untruncated.}

\\end{aligned}

]

&#x20;



\------





\#### Theorem Statement (Cross-chunk consistency review)





\##Claude response



\\section\*{Cross-chunk consistency review}



&#x20; \\subsection\*{(1) \\textsc{Notation}}



&#x20; $\\mathbf{FLAGGED.}$ Most symbols are consistent, but $\\epsilon\_\\times$ (appearing in both $\\Delta\_\\sigma :=

&#x20; 4(|\\hat\\sigma^2-\\sigma\_\\varepsilon^2|L^2 + 2L^3\\epsilon\_\\times)/\\lambda\_{\\min}$ and $\\Delta\_\\sigma^{\\mathrm{sharp}} :=

&#x20;  8L^3\\epsilon\_\\times/\\lambda\_{\\min}$) is $\\mathbf{never\\ defined}$ in \\texttt{theorem\_statements.tex}. Readers cannot

&#x20; tell whether $\\epsilon\_\\times$ scales with $m\_k$, $T$, or is $\\Theta(1)$ — which matters for check (8).



&#x20; Minor: two uses of "$\\lambda$" — $\\lambda$ inside $L\_W := \\log(1+WR\_\\cA^2/(\\lambda r))$ (ridge parameter) versus

&#x20; $\\lambda\_{\\min}$ (eigengap). Also $W$ in $O(WV)$ vs.\\ $W\_{\\mathrm{det}}$ in Thm\~\\ref{thm:spsc\_adaptive} — two

&#x20; different windows. Worth disambiguating.



&#x20; Also: Thm\~\\ref{thm:spsc\_regret} writes $\\tilO(r\\sqrt{KTL\_W})$ while Thm\~\\ref{thm:spsc\_adaptive} writes

&#x20; $\\tilO(r\\sqrt{KT})$ — reconcilable since $L\_W$ is a log and is absorbed by $\\tilO$, but inconsistent presentation.



&#x20; \\subsection\*{(2) \\textsc{Thm 1 vs Cor misspec}}



&#x20; $\\mathbf{VERIFIED.}$ The sources are disjoint:

&#x20; $$\\Delta\_\\sigma ;\\leftarrow; \\text{bias in } \\widehat M\_k \\text{ from noise-variance / probe-moment misspec},$$

&#x20; $$O!\\Bigl(R\_\\cA \\sum\_k \\epsilon\_k^\\perp (1+S\_w^2/\\lambda\_{\\min}) n\_k\\Bigr) ;\\leftarrow; \\text{regret from un-trackable

&#x20;  } \\theta\_t^\\perp \\text{ direction}.$$

&#x20; The strengthened eigengap $\\lambda\_{\\min}\\ge 4C\_{\\mathrm{sub}}\\sqrt{\\log(2d/\\delta)/m\_k}+12 S\_w\\epsilon\_k^\\perp$

&#x20; absorbs the new estimation bias, leaving $\\Delta\_\\sigma$ untouched. No double-counting, provided $\\epsilon\_\\times$

&#x20; (used inside $\\Delta\_\\sigma$) does not itself include an $\\epsilon\_k^\\perp$ contribution — which cannot be verified

&#x20; without the missing definition flagged in (1).



&#x20; \\subsection\*{(3) \\textsc{Thm 1 vs Remark variance\_misspec}}



&#x20; $\\mathbf{VERIFIED.}$ Direct subtraction:

&#x20; $$\\Delta\_\\sigma - \\Delta\_\\sigma^{\\mathrm{sharp}} ;=; \\frac{4|\\delta\_\\sigma|L^2}{\\lambda\_{\\min}} ;\\ge; 0,$$

&#x20; so $\\Delta\_\\sigma^{\\mathrm{sharp}}\\le \\Delta\_\\sigma$ identically. The remark's claim that the sharp version "drops

&#x20; $\\delta\_\\sigma$" holds because for isotropic Gaussian probes $\\E\[u u^\\top]=I\_d/(d+2) \\cdot \\text{(scalar)}$, so the

&#x20; $\\delta\_\\sigma$-component of the bias matrix is a scaled identity and does not perturb eigenvectors — consistent with

&#x20; being eliminated after projector stability.



&#x20; \\subsection\*{(4) \\textsc{Thm 1 vs Thm spsc\_adaptive — CRITICAL}}



&#x20; $\\boxed{\\mathbf{FLAGGED.}}$ The "fixed probe rate $\\mu\\in(0,1)$" claim is $\\mathbf{inconsistent}$ with retaining the

&#x20; $\\tilO(K^{1/3}T^{2/3})$ rate if $\\mu$ is a universal constant. Compute:



&#x20; $$\\text{Oracle (Thm\~\\ref{thm:spsc\_regret}):}\\quad m\_k = \\Big\\lceil (B\\ell\_k/(2A))^{2/3}\\Big\\rceil ;\\Longrightarrow;

&#x20; m\_k \\asymp \\ell\_k^{2/3},\\quad \\sum\_k m\_k \\cdot c ;\\le; c,K^{1/3}T^{2/3};\\text{by Jensen.}$$

&#x20; $$\\text{Fixed-}\\mu\\text{ (Thm\~\\ref{thm:spsc\_adaptive}):}\\quad \\E\[m\_k]=\\mu \\ell\_k ;\\Longrightarrow; \\text{probe cost}

&#x20; ;=; c\\mu T ;=; \\Theta(T).$$



&#x20; For constant $\\mu\\in(0,1)$, the probe cost alone is $\\Theta(T)$, which $\\mathbf{dominates}$ $\\tilO(K^{1/3}T^{2/3})$ in

&#x20;  the entire informative regime $K=o(T^{1/2}/r^{3/2})$, since

&#x20; $$\\mu T ;\\gg; K^{1/3}T^{2/3}\\ \\iff\\ \\mu ;\\gg; K^{1/3}T^{-1/3} ;\\to; 0.$$



&#x20; Matching the rate requires $\\mu$ to scale with $(T,K)$. Balancing probe cost and estimation regret:

&#x20; $$\\underbrace{\\sum\_k R\_\\cA S\_w \\ell\_k \\varepsilon\_k}{\\asymp R\\cA S\_w \\sum\_k \\sqrt{\\ell\_k/\\mu}\\le R\_\\cA

&#x20; S\_w\\sqrt{KT/\\mu}} ;\\asymp; c\\mu T ;\\Longleftrightarrow; \\mu^\\star ;\\asymp; K^{1/3}T^{-1/3}.$$



&#x20; Hence the statement is only valid under either (a) $\\mu = \\mu(T,K) \\asymp K^{1/3}T^{-1/3}$, or (b) reinterpretation of

&#x20;  "fixed" as "non-adaptive but $(T,K)$-dependent." Under the literal reading "$\\mu\\in(0,1)$ constant," the regret term

&#x20; $O(c\\mu T)$ is missing from the stated bound. $\\mathbf{The\\ theorem\\ statement\\ is\\ either\\ wrong\\ or\\ needs\\

&#x20; qualification.}$



&#x20; \\subsection\*{(5) \\textsc{Thm 1 vs Thm regret\_lb}}



&#x20; $\\mathbf{VERIFIED.}$ Dominant UB term in informative regime: $\\tilO(K^{1/3}T^{2/3})$. LB:

&#x20; $\\Omega(c^{1/3}(R\_\\cA\\sigma\_\\varepsilon)^{2/3}T^{2/3})$. Both have the $T^{2/3}$ exponent; the $c^{1/3}$ factor in the

&#x20;  LB matches the UB's cost dependence via $A=2R\_\\cA S\_w+c$ inside $m\_k \\propto (B/(2A))^{2/3}$. Rates $\\mathbf{match}$

&#x20; up to constants / $K$-dependence not characterized by the LB.



&#x20; \\subsection\*{(6) \\textsc{Regime overlap}}



&#x20; $\\mathbf{VERIFIED.}$ UB regime: $K = o(\\min{T^{1/2}/r^{3/2},, d^2/r^2})$. LB regime: $d \\ge d\_0 r T^{1/3}$.

&#x20; $$d \\ge d\_0 r T^{1/3} ;\\Longrightarrow; d^2/r^2 \\ge d\_0^2 T^{2/3} ;\\gg; T^{1/2}/r^{3/2}\\ \\text{(for }r,d\_0\\text{

&#x20; fixed, large }T\\text{)},$$

&#x20; so the binding UB condition is $K = o(T^{1/2}/r^{3/2})$, which is compatible with the LB regime. No conflict.



&#x20; \\subsection\*{(7) \\textsc{Cor rank\_adaptive vs Thm 1}}



&#x20; $\\mathbf{VERIFIED\\ (modulo\\ logs).}$ $C\_{\\mathrm{sub}}=8R\_X/\\lambda\_{\\min}$, $R\_X=L^2 R\_s+S\_w^2$, $B=2C\_{\\mathrm{sub}}

&#x20;  S\_w R\_\\cA \\sqrt{\\log(d/\\delta)}$ are functions of $(d,T,\\delta,R\_\\cA,S\_w,\\sigma\_\\varepsilon,\\lambda\_{\\min})$ — none

&#x20; depends on whether $r$ is known. The union bound turns $\\delta\\to 2\\delta$ (or similar), shifting $\\log(1/\\delta)$ by

&#x20; a constant that $\\tilO$ absorbs. Constants are $\\mathbf{literally\\ unchanged}$; implicit log factors grow by $O(1)$.



&#x20; \\subsection\*{(8) \\textsc{Informative regime}}



&#x20; $\\mathbf{FLAGGED.}$ For the bound to be $o(T)$ term-by-term:

&#x20; $$(i)\\ r\\sqrt{KTL\_W}=o(T) \\iff K=o(T/(r^2 L\_W));\\quad (ii)\\ K^{1/3}T^{2/3}=o(T) \\iff K=o(T);$$

&#x20; $$(iii)\\ WV=o(T) \\iff V=o(T/W);\\quad (iv)\\ T\\Delta\_\\sigma=o(T) \\iff \\Delta\_\\sigma=o(1).$$



&#x20; The theorem states (i)--(iii) via $K=o(\\min{T^{1/2}/r^{3/2}, d^2/r^2})$ and $V=o(r\\sqrt{KT}/W)$ but is

&#x20; $\\mathbf{silent\\ on\\ (iv)}$. Since $L^2=2d\\log(4T/\\delta)$, we have $L^3=\\Theta((d\\log T)^{3/2})$, so

&#x20; $$\\Delta\_\\sigma ;=; \\Theta!\\left(\\frac{|\\delta\_\\sigma|, d\\log T + (d\\log

&#x20; T)^{3/2}\\epsilon\_\\times}{\\lambda\_{\\min}}\\right),$$

&#x20; which is $\\omega(1)$ unless $\\epsilon\_\\times$ and $\\delta\_\\sigma$ vanish with $T$. The stated "informative regime" is

&#x20; $\\mathbf{incomplete}$: a condition of the form $\\Delta\_\\sigma = o(1)$ (or equivalently, decay of $\\epsilon\_\\times$ and

&#x20;  $\\delta\_\\sigma$) must be appended for the bound to be non-trivial.



&#x20; \\subsection\*{(9) \\textsc{Piecewise-constant vs LDS}}



&#x20; $\\mathbf{VERIFIED.}$ The $O(WV)$ term appears in Thm\~\\ref{thm:spsc\_regret}, Thm\~\\ref{thm:spsc\_adaptive},

&#x20; Cor\~\\ref{cor:rank\_adaptive} (inherits), and Cor\~\\ref{cor:misspec} (inherits). Under stable LDS with stationary

&#x20; innovations, $|\\theta\_{s+1}-\\theta\_s|=\\Theta(1)$ per step, giving $V=\\Theta(T)$ and

&#x20; $WV=\\Theta(WT)=\\omega(r\\sqrt{KT})$. $\\mathbf{No}$ theorem or remark asserts the LDS regime is informative; the paper

&#x20; is internally consistent in restricting informative claims to piecewise-constant $w\_t$ (where $V\\le 2KS\_w$).



&#x20; \\bigskip

&#x20; $\\mathbf{Summary:}$ $\\boxed{4 \\text{ FLAG}}$ ${(1), (4), (8)}$ plus partial-FLAG on $(1)$ for undefined

&#x20; $\\epsilon\_\\times$. Check $(4)$ is the load-bearing issue: the adaptive theorem's probe-rate claim needs either a

&#x20; rewrite to $\\mu\\asymp K^{1/3}T^{-1/3}$ or an explicit statement that $\\mu$ is allowed to depend on $(T,K)$.







\### GPT Resposne



\[

\\textbf{Cross-Chunk Consistency Review}

]



\[

\\textbf{(1)}\\quad \\mathrm{VERIFIED}; \\text{Among the listed symbols, no symbol is reused with a conflicting meaning across the statements: }\\Delta\_\\sigma,V,W,K,\\varepsilon\_k,R\_{\\mathcal A},S\_w,\\lambda\_{\\min},L,L\_W,L\_y,L\_\\varepsilon,R\_X,C\_{\\mathrm{sub}},\\Pi\_{\\mathrm{HP}}\\text{ are used consistently, and }V\_{k,t}(W)\\text{ / }W\_{\\mathrm{det}}\\text{ are distinct derived notations rather than redefinitions.}

]



\[

\\textbf{(2)}\\quad \\mathrm{VERIFIED}; \\text{The }O(T\\Delta\_\\sigma)\\text{ term in Theorem }(\\mathrm{spsc\_regret})\\text{ only tracks variance/cross-correlation bias through }\\hat\\sigma^2-\\sigma\_\\varepsilon^2\\text{ and }\\epsilon\_\\times,\\text{ whereas Corollary }(\\mathrm{misspec})\\text{ adds a new }\\epsilon\_k^\\perp\\text{-dependent approximation term, so there is no statement-level double-counting.}

]



\[

\\textbf{(3)}\\quad \\mathrm{VERIFIED}; \\text{Since }\\Delta\_\\sigma=4\\bigl(|\\delta\_\\sigma|L^2+2L^3\\epsilon\_\\times\\bigr)/\\lambda\_{\\min}=4|\\delta\_\\sigma|L^2/\\lambda\_{\\min}+8L^3\\epsilon\_\\times/\\lambda\_{\\min}\\ge 8L^3\\epsilon\_\\times/\\lambda\_{\\min}=\\Delta\_\\sigma^{\\mathrm{sharp}},\\text{ the remark is a Gaussian-specialized sharpening of the conservative theorem bound, not a contradiction saying the theorem was wrong to include }\\delta\_\\sigma\\text{ in the general case.}

]



\[

\\textbf{(4)}\\quad \\mathrm{FLAGGED}; \\text{Theorem }(\\mathrm{spsc\_adaptive})\\text{ says the adaptive method uses a fixed probe rate }\\mu\\in(0,1),\\text{ but under the costed regret definition this implies }|\\mathcal T\_{\\mathrm{probe}}|=\\Theta(\\mu T)\\text{ and hence a linear }c\\mu T\\text{ probe-cost contribution, so matching Theorem }(\\mathrm{spsc\_regret})\\text{'s }\\tilde O(K^{1/3}T^{2/3})\\text{ rate requires }\\mu=\\mu\_{K,T}\\to 0\\text{ rather than a fixed constant.}

]



\[

\\textbf{(5)}\\quad \\mathrm{UNSURE}; \\text{Theorem }(\\mathrm{regret\_lb})\\text{ certifies the }T^{2/3}\\text{ cost exponent in the hard-projection large-}d\\text{ regime, but it does not state any }K\\text{-dependence, so I need to know whether its lower-bound construction fixes }K=\\Theta(1)\\text{ or proves a }K^{1/3}\\text{-dependent lower bound to decide if it fully matches Theorem }(\\mathrm{spsc\_regret}).

]



\[

\\textbf{(6)}\\quad \\mathrm{FLAGGED}; \\text{The regimes of Theorem }(\\mathrm{spsc\_regret})\\text{ and Theorem }(\\mathrm{regret\_lb})\\text{ only partially overlap—for example }(r,d,K)=(1,T^{1/4},T^{1/8})\\text{ satisfies the former but violates }d\\ge d\_0T^{1/3},\\text{ while }(r,d,K)=(1,2d\_0T^{1/3},T^{0.6})\\text{ satisfies the latter but violates }K=o(T^{1/2})\\text{—so any blanket rate-matching claim is moot outside that overlap.}

]



\[

\\textbf{(7)}\\quad \\mathrm{VERIFIED}; \\text{In Corollary }(\\mathrm{rank\_adaptive}),\\text{ “unchanged” is internally consistent because on the stated good event thresholding recovers }\\hat r=r,\\text{ so the same true-rank constants }C\_{\\mathrm{sub}},R\_X,B\\text{ are used as in Theorem }(\\mathrm{spsc\_regret}),\\text{ with only an extra union-bound failure term.}

]



\[

\\textbf{(8)}\\quad \\mathrm{VERIFIED}; \\text{The dependency chain is internally consistent: Lemma }(\\mathrm{G\_bound})\\text{ gives }|G\_t|\*{\\mathrm{op}}\\le R\_X\\text{ on }\\mathcal A\_t,\\text{ Theorem }(\\mathrm{matrix\_bernstein})\\text{ converts this into an }O!\\left(R\_X\\sqrt{\\log/m\_k}\\right)\\text{ deviation, and Corollary }(\\mathrm{projector})\\text{ then applies Davis--Kahan with gap }\\lambda\*{\\min}\\text{ to produce }C\_{\\mathrm{sub}}=8R\_X/\\lambda\_{\\min}.

]



\[

\\textbf{(9)}\\quad \\mathrm{FLAGGED}; \\text{The “informative when” clause in Theorem }(\\mathrm{spsc\_regret})\\text{ is not the full intersection of sublinear-term requirements because it does not explicitly include the necessary condition }\\Delta\_\\sigma=o(1)\\text{ for }O(T\\Delta\_\\sigma)=o(T),\\text{ so the statement is incomplete as written if “informative” means all additive terms are }o(T).

]



\[

\\textbf{(10)}\\quad \\mathrm{VERIFIED}; \\text{Within the provided theorem/corollary/remark statements, nothing contradicts Theorem }(\\mathrm{spsc\_regret})\\text{'s claim that the bound is interesting only in the piecewise-constant regime: no other statement says the stationary stable-LDS regime }V=\\Theta(T)\\text{ is still informative.}

]





