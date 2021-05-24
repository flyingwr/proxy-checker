from aiohttp_socks import ProxyConnector, ProxyType
from python_socks._errors import ProxyError

import aiohttp, asyncio
loop = asyncio.get_event_loop()
timeout = aiohttp.ClientTimeout(total=15.0)

urls = (
	"https://api.proxyscrape.com?request=displayproxies&proxytype=socks5&timeout=5000",
	"https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt"
)

async def fetch_proxies():
	result = []
	async with aiohttp.ClientSession() as session:
		for url in urls:
			async with session.get(url) as response:
				if response.status == 200:
					result.extend(
						(tuple(proxy.strip().split(":")) for proxy in (await response.text()).split("\n") if ":" in proxy)
					)
	return result

async def check_proxy(host, port):
	proxy = f"{host}:{port}"

	async def on_request_start(_, ctx, __):
		ctx.start = loop.time()

	result = dict(passed=False)
	async def on_request_end(_, ctx, __):
		print(f"[Proxy {proxy}] session passed ({loop.time() - ctx.start:.2f}s)")
		result.update(dict(passed=True, proxy=proxy))

	trace_config = aiohttp.TraceConfig()
	trace_config.on_request_start.append(on_request_start)
	trace_config.on_request_end.append(on_request_end)

	try:
		async with aiohttp.ClientSession(connector=ProxyConnector(
			proxy_type=ProxyType.SOCKS5, host=host, port=port, rdns=True
		), timeout=timeout, trace_configs=[trace_config]) as session:
			resp = await session.get("https://google.com")
			resp.close()
	except Exception:
		print(f"[Proxy {proxy}] session failed")

	return result

if __name__ == "__main__":
	print("Fetching some proxies")

	proxy_list = loop.run_until_complete(fetch_proxies())
	if proxy_list:
		print(f"Found list of {len(proxy_list)} proxies")

		result = loop.run_until_complete(asyncio.gather(*(check_proxy(host, int(port)) for host, port in proxy_list)))
		with open("./out.txt", "w") as f:
			f.write("\n".join((info["proxy"] for info in filter(lambda d: d["passed"], result))))
	else:
		print("Found no proxy list")