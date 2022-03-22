import goprohero as gopro

camera = gopro.GoProHero('192.168.0.1', password='a12345678')
camera.command('record', 'on')
status = camera.status()
