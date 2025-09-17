# Configuração da Integração com Google

## Pré-requisitos

1. **Conta Google** com acesso ao Google Sheets e Google Forms
2. **Projeto no Google Cloud Console**
3. **Service Account** configurado

## Passos para Configuração

### 1. Criar Projeto no Google Cloud Console

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative as seguintes APIs:
   - Google Sheets API
   - Google Forms API

### 2. Criar Service Account

1. No Google Cloud Console, vá para "IAM & Admin" > "Service Accounts"
2. Clique em "Create Service Account"
3. Dê um nome como "sistema-rpz-integration"
4. Clique em "Create and Continue"
5. Pule as etapas de permissões (vamos configurar depois)
6. Clique em "Done"

### 3. Gerar Chave JSON

1. Na lista de Service Accounts, clique no que você criou
2. Vá para a aba "Keys"
3. Clique em "Add Key" > "Create new key"
4. Selecione "JSON"
5. Clique em "Create"
6. O arquivo JSON será baixado automaticamente

### 4. Configurar Credenciais

1. Renomeie o arquivo baixado para `google_credentials.json`
2. Mova o arquivo para a pasta `config/` do projeto
3. O arquivo deve estar em: `config/google_credentials.json`

### 5. Compartilhar Planilha e Formulários

1. **Planilha do Google Sheets:**
   - Abra a planilha: https://docs.google.com/spreadsheets/d/1NauRIwyzMaObJ46zNLj0c-1aS7pHzUwXWaM6DSiAjHs/edit#gid=0
   - Clique em "Compartilhar"
   - Adicione o email do Service Account (encontrado no arquivo JSON)
   - Dê permissão de "Editor"

2. **Google Forms:**
   - Para cada formulário listado no código, adicione o email do Service Account
   - Dê permissão de "Editor"

### 6. Instalar Dependências

```bash
pip install -r requirements.txt
```

## Estrutura da Planilha

A planilha deve ter as seguintes colunas (na ordem correta):

1. ID
2. Nome
3. Data de Admissão
4. CPF
5. CNH
6. RG
7. Código SAP
8. Operação
9. CTPS
10. Série
11. Data de Nascimento
12. Primeira CNH
13. Data de Expedição
14. Vencimento CNH
15. Done MOPP
16. Vencimento MOPP
17. Done Toxicológico CLT
18. Vencimento Toxicológico CLT
19. Done ASO Semestral
20. Vencimento ASO Semestral
21. Done ASO Periódico
22. Vencimento ASO Periódico
23. Done Buonny
24. Vencimento Buonny
25. Telefone
26. Endereço
27. Filiação
28. Estado Civil
29. Filhos
30. Cargo
31. Empresa
32. Status
33. Conf Jornada
34. Conf Fecham
35. Done Toxicológico CNH
36. Vencimento Toxicológico CNH
37. Email

## Logs

Os logs da integração são salvos em:
- `logs/verif_forms_google.txt`

## Teste da Integração

Para testar se a integração está funcionando:

1. Certifique-se de que o arquivo `config/google_credentials.json` existe
2. Inicie a aplicação: `python app.py`
3. Acesse a página de motoristas
4. Tente criar um novo motorista
5. Verifique os logs em `logs/verif_forms_google.txt`

## Troubleshooting

### Erro: "Arquivo de credenciais não encontrado"
- Verifique se o arquivo `config/google_credentials.json` existe
- Verifique se o caminho está correto

### Erro: "Permission denied"
- Verifique se o Service Account tem permissão na planilha e formulários
- Verifique se o email do Service Account foi adicionado corretamente

### Erro: "API not enabled"
- Verifique se as APIs do Google Sheets e Google Forms estão ativadas no projeto

### Erro: "Invalid credentials"
- Verifique se o arquivo JSON está correto
- Verifique se o projeto tem as APIs necessárias ativadas 