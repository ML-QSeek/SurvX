# 开多10手RB2410（螺纹钢）
result = execute_futures_open_long('rb2410', 10)

# TWAP开多
result = execute_futures_open_long('rb2410', 10, algorithm='TWAP', slices=5, interval=30)

# 限价开空
result = execute_futures_open_short('rb2410', 5, price_type='3', limit_price=3450)

# 平多
result = execute_futures_close_long('rb2410', 5)

# 套利：多近月空远月
result = execute_futures_spread('rb2410', 'rb2501', 5, 5, 'long_short')