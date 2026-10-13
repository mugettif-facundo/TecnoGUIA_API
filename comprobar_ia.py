import ia_local
if __name__=='__main__':
 estado=ia_local.estado()
 print(estado['mensaje'])
 print('Modelo configurado:',estado['modelo'])
 if estado['conectado'] and not estado['modelo_disponible']:
  print('En CMD ejecutá: ollama pull '+estado['modelo'])
