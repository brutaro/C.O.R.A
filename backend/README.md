# C.O.R.A. Backend

Backend proprio do `C.O.R.A.` - `Conflito de Interesses: Orientacao, Registro e Analise`.

Este backend foi criado como copia inicial da base da L.A.R.A., mas passa a ser mantido como estrutura independente dentro de `CORA/backend`.

Diretrizes desta etapa:

- nao compartilhar scripts operacionais com a L.A.R.A.;
- ajustar esta base exclusivamente para o produto de conflito de interesses;
- apontar consultas apenas para `notas_conflito_interesse`;
- manter Redis como memoria contextual;
- manter suporte a exportacao em PDF;
- usar Firebase Auth no backend e Firestore para historico;
- manter esta pasta pronta para futura extracao para repositorio proprio;
- nao introduzir plataforma de observabilidade dedicada nesta fase.

Estrutura esperada:

- `main.py`
- `auth.py`
- `src/`
- `prompts/`
- `reportlab/`

Observacao:

- o frontend do produto fica em `CORA/frontend`, fora desta pasta.
- a configuracao de seguranca do Firestore fica em `CORA/firestore.rules`.
