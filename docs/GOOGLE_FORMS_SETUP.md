# 🔧 Configuração do Google Forms - Sistema RPZ

## ⚠️ **Problema Atual:**
```
Request had insufficient authentication scopes
```

## 🎯 **Solução:**

### **1. Configurar Google Cloud Console**

1. **Acesse:** [Google Cloud Console](https://console.cloud.google.com/)
2. **Selecione seu projeto**
3. **Vá para:** APIs & Services > Library
4. **Ative as seguintes APIs:**
   - ✅ Google Sheets API
   - ✅ Google Forms API
   - ✅ Google Drive API

### **2. Configurar Service Account**

1. **Vá para:** APIs & Services > Credentials
2. **Crie uma nova Service Account** (se não existir)
3. **Baixe o arquivo JSON** de credenciais
4. **Renomeie para:** `credentials.json`
5. **Coloque na pasta:** `credentials/`

### **3. Configurar Permissões dos Formulários**

**IMPORTANTE:** Cada formulário precisa ser compartilhado com o Service Account!

1. **Abra cada formulário do Google Forms**
2. **Clique em:** ⋮ (três pontos) > Configurações
3. **Vá para:** Respostas > Adicionar colaboradores
4. **Adicione o email da Service Account** com permissão de **Editor**

### **4. Encontrar o Email da Service Account**

No arquivo `credentials.json`, procure por:
```json
{
  "client_email": "sua-service-account@projeto.iam.gserviceaccount.com"
}
```

### **5. Compartilhar Formulários**

Para cada formulário configurado no sistema:
- `1kHjVfLPHnHWaHgeWMa2JV_fAYflFa2P_y3pnqJWHfGI`
- `1UXMvIgpMrc8adfNNeEOgaL02hHQpWdi1r9TTs1FvLVc`
- `1ZZk78DbOOMMn_MO8RBPcPsE5juq51MxnOwdzHu2jLv8`
- `1rU83EUmsEXPOGG-XHOmfJAztbYWVjqQNxPaGQNMX7D4`
- `1FVyTkp70R3PIINfnlNQuUj3QvvJW5VOY9OsRonkyTaE`
- `1pLmWsw7PdKUJt_cWeLCUET11TeDjsjG0FlZmN3pJad4`
- `1AfrEwnT6k8uJ6fHyNRrAGDXrhvj_A1tkIoaPNVkw7iM`
- `188ilDeyjtQmzuXIT4beXZBYnbPIgci0NjkuNQrTEv30`
- `1htb51Sa5gMgZxbOgns6pavpV8gbRLaHShutgD5RQirs`

**Compartilhe cada um com o email da Service Account**

### **6. Verificar Configuração**

1. **Execute o sistema**
2. **Adicione um novo motorista**
3. **Verifique os logs:** `logs/verif_forms_google.txt`

### **7. Escopos Corrigidos**

O código agora inclui os escopos corretos:
```python
scope = [
    'https://spreadsheets.google.com/feeds',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/forms',
    'https://www.googleapis.com/auth/forms.body',           # ✅ NOVO
    'https://www.googleapis.com/auth/forms.responses.readonly'  # ✅ NOVO
]
```

## 🎉 **Resultado Esperado:**

Após a configuração, você deve ver nos logs:
```
[2025-08-05 XX:XX:XX] Formulário 1kHjVfLPHnHWaHgeWMa2JV_fAYflFa2P_y3pnqJWHfGI atualizado com sucesso
[2025-08-05 XX:XX:XX] Formulário 1UXMvIgpMrc8adfNNeEOgaL02hHQpWdi1r9TTs1FvLVc atualizado com sucesso
...
```

## 📞 **Suporte:**

Se ainda houver problemas:
1. Verifique se todos os formulários foram compartilhados
2. Confirme se o email da Service Account está correto
3. Aguarde alguns minutos após compartilhar (pode levar tempo para propagar) 