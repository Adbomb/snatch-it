-- Короткая запись больших чисел для игрока (D29): 950 / 1.2K / 3.4M / 5.6B / 7.8T / 9.1Qa.
-- Одна функция на всю игру — и вывески мира, и интерфейс. Ни от чего не зависит.

local SUFFIXES = {
	{ 1e15, "Qa" },
	{ 1e12, "T" },
	{ 1e9, "B" },
	{ 1e6, "M" },
	{ 1e3, "K" },
}

local NumberFormat = {}

function NumberFormat.Short(value: number): string
	local sign = if value < 0 then "-" else ""
	local abs = math.abs(value)
	for _, entry in SUFFIXES do
		if abs >= entry[1] then
			-- Одна цифра после точки, без «.0»: 1K, 1.5K, 12.3M.
			local scaled = math.floor(abs / entry[1] * 10) / 10
			local text = if scaled % 1 == 0 then ("%d"):format(scaled) else ("%.1f"):format(scaled)
			return sign .. text .. entry[2]
		end
	end
	return sign .. ("%d"):format(math.floor(abs))
end

return NumberFormat
