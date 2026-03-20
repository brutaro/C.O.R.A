# 📱 Guia de Teste Mobile

## 1. Teste Rápido - DevTools do Navegador (Chrome/Edge)

### Passos:
1. Abra o app em `http://localhost:3000`
2. Pressione **F12** (ou **Cmd+Option+I** no Mac)
3. Clique no ícone de dispositivo móvel (ou **Cmd+Shift+M**)
4. Selecione um dispositivo:
   - **iPhone 12/13/14 Pro** (390x844)
   - **Samsung Galaxy S20** (360x800)
   - Ou ajuste manualmente para **375px** de largura

### O que testar:
- ✅ Scroll da lista de conversas (deve rolar suavemente)
- ✅ Abrir/fechar sidebar (botão hambúrguer)
- ✅ Overlay escuro ao abrir sidebar (deve aparecer)
- ✅ Fechar sidebar tocando no overlay
- ✅ Tamanho dos botões (mínimo 44x44px)
- ✅ Input não faz zoom ao focar (font-size: 16px)
- ✅ Chat scrolla corretamente
- ✅ Layout não quebra em telas pequenas

## 2. Teste em Dispositivo Real

### Opção A: Reiniciar React com HOST=0.0.0.0

```bash
# Pare o servidor React atual (Ctrl+C)
# Depois inicie com:
cd web/frontend
HOST=0.0.0.0 npm start
```

### Opção B: Usar o IP local diretamente

Se o React já está rodando, acesse no celular:
- **URL**: `http://192.168.15.3:3000`
- Certifique-se de que o celular está na mesma rede Wi-Fi

### O que testar no dispositivo real:
- ✅ Scroll com toque (deve ter inércia suave)
- ✅ Overlay responde ao toque
- ✅ Botões são fáceis de tocar (não muito pequenos)
- ✅ Safe area funciona (input não fica cortado em iPhones com notch)
- ✅ Performance do scroll (deve ser fluido)
- ✅ Sidebar abre/fecha sem travamentos

## 3. Breakpoints de Teste

Teste em diferentes larguras:
- **320px** - iPhone SE (menor tela comum)
- **375px** - iPhone 12/13/14
- **390px** - iPhone 12/13/14 Pro
- **414px** - iPhone Plus/Pro Max
- **768px** - Tablet (iPad portrait)

## 4. Checklist de Funcionalidades Mobile

### Sidebar
- [ ] Abre com botão hambúrguer
- [ ] Fecha ao tocar no overlay
- [ ] Fecha ao tocar no botão X
- [ ] Lista de conversas faz scroll
- [ ] Menu de opções (três pontos) funciona
- [ ] Edição de título funciona
- [ ] Exclusão de conversa funciona

### Chat
- [ ] Mensagens aparecem corretamente
- [ ] Scroll do chat funciona
- [ ] Input fica visível (não cortado)
- [ ] Botão de enviar funciona
- [ ] Não faz zoom ao focar no input

### Layout Geral
- [ ] Não há scroll horizontal indesejado
- [ ] Elementos não ficam cortados
- [ ] Texto é legível
- [ ] Espaçamentos adequados

## 5. Problemas Comuns e Soluções

### Scroll não funciona
- Verifique se `-webkit-overflow-scrolling: touch` está aplicado
- Confirme que o elemento tem `overflow-y: auto` e altura definida

### Sidebar não fecha
- Verifique se o overlay está sendo renderizado
- Confirme que o `onClick` do overlay está funcionando

### Zoom ao focar no input
- Verifique se `font-size: 16px` está aplicado
- iOS faz zoom automático se font-size < 16px

### Layout quebrado
- Verifique se `max-width: 100vw` está aplicado
- Confirme que não há elementos com largura fixa maior que a tela

## 6. Ferramentas Úteis

- **Chrome DevTools**: Device Mode + Throttling
- **Safari Web Inspector**: Para testar em iPhone real
- **Responsive Design Mode**: Firefox DevTools
- **BrowserStack**: Teste em dispositivos reais na nuvem (pago)

