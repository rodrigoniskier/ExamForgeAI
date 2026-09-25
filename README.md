# ExamForgeAI

### Banco de questões e avaliações com apoio de IA

Edição pública de portfólio com dados inteiramente sintéticos. O código não depende de sistemas originais, bases institucionais ou informações pessoais.

**Stack:** Django · PostgreSQL · Structured Output · Assessment

## O produto

Rascunho e revisão simulados; edição humana; cópia segura dos itens-base; aprovação; montagem com itens aprovados; gabarito alfabético; exportação Blackboard.

## Demonstração

Ative `PORTFOLIO_DEMO=1` **somente em um banco dedicado**. O acesso é feito pelo botão da tela inicial; não há senha pública nem acesso administrativo privilegiado.

32 questões originais, 4 componentes, 2 avaliações montadas.

A publicação online e os testes em PostgreSQL/Vercel ainda precisam ser concluídos. Nenhuma URL de aplicação é anunciada como funcional antes dessa verificação.

## Execução local

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export PORTFOLIO_DEMO=1
export DEBUG=1
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Os bancos locais são ignorados pelo Git. `seed_demo` é idempotente: executá-lo novamente não duplica a base. Para restaurar uma demonstração, use um **novo banco vazio dedicado**, execute as migrations (Django) e repita a carga; não execute reset em uma base de produção.

## Publicação na Vercel

O arquivo `vercel.json` encaminha a aplicação Python e serve os assets estáticos. Configure exclusivamente no ambiente da plataforma:

- `PORTFOLIO_DEMO=1`
- `SECRET_KEY`: valor aleatório próprio desta implantação
- `DATABASE_URL`: PostgreSQL dedicado, com TLS
- `DEBUG=0`
- `ALLOWED_HOSTS`: hostname exato da implantação
- `CSRF_TRUSTED_ORIGINS`: origem HTTPS exata
- `USE_FAKE_AI=1` — o modo demo também força a IA simulada independentemente desta flag.

Execute a carga inicial antes de abrir a URL pública. A aplicação recusa execução na Vercel sem banco persistente e chave de sessão. Não use SQLite no filesystem temporário da hospedagem.

## Limites da demo

- Painel administrativo bloqueado e contas demonstrativas sem privilégios perigosos.
- Dados de exemplo identificados como sintéticos; visitantes devem usar apenas conteúdo fictício.
- Novos uploads bloqueados.
- Operações de escrita limitadas; os registros-base permanecem disponíveis.
- CSRF e headers de segurança ativos.
- Não é um ambiente de produção nem um serviço para informações confidenciais.

## Validação

```bash
python manage.py test
```

Testes de autorização, CSRF, integridade dos dados demonstrativos e fluxos principais. Dependabot e GitHub Actions preservados.

Consulte [SECURITY.md](SECURITY.md). Nunca faça commit de `.env`, tokens, bancos, exports ou credenciais.
