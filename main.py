import os

# Trên Android: tự động điều chỉnh HEIGHT logical để khớp tỉ lệ màn hình điện thoại,
# tránh letterbox đen ở trên/dưới mà không bị méo hình.
# QUAN TRỌNG: phải chạy TRƯỚC `from game import Game` để các `from config import *`
# trong các module khác thấy được giá trị HEIGHT mới.
if 'ANDROID_ARGUMENT' in os.environ or 'ANDROID_ROOT' in os.environ:
    import pygame
    pygame.display.init()
    info = pygame.display.Info()
    sw, sh = info.current_w, info.current_h
    if sw > 0 and sh > 0:
        import config
        # Giữ WIDTH = 400, scale HEIGHT theo aspect ratio của phone
        old_height = config.HEIGHT
        config.HEIGHT = int(config.WIDTH * sh / sw)
        # Scale gap giữa pipe theo tỉ lệ HEIGHT để layout cân đối
        scale = config.HEIGHT / old_height
        config.TUBE_GAP = int(config.TUBE_GAP * scale)
    pygame.display.quit()

from game import Game

if __name__ == "__main__":
    game_instance = Game()
    game_instance.run()
