-- Регистр для русского текста: string.upper и string.lower в Luau меняют только латиницу, кириллицу не трогают.
-- Ни от чего не зависит.

local TextCase = {}

function TextCase.Upper(text: string): string
	local out = {}
	for _, code in utf8.codes(text) do
		if (code >= 0x0430 and code <= 0x044F) or (code >= 0x61 and code <= 0x7A) then
			code -= 0x20 -- а…я → А…Я, латиница
		elseif code == 0x0451 then
			code = 0x0401 -- ё → Ё
		end
		table.insert(out, utf8.char(code))
	end
	return table.concat(out)
end

-- Строчные буквы (для поиска): А…Я → а…я, Ё → ё, латиница; fold — ещё и ё → е («ёж» находится по «еж»).
function TextCase.Lower(text: string, fold: boolean?): string
	local out = {}
	for _, code in utf8.codes(text) do
		if (code >= 0x0410 and code <= 0x042F) or (code >= 0x41 and code <= 0x5A) then
			code += 0x20 -- А…Я → а…я, латиница
		elseif code == 0x0401 then
			code = 0x0451 -- Ё → ё
		end
		if fold and code == 0x0451 then
			code = 0x0435
		end
		table.insert(out, utf8.char(code))
	end
	return table.concat(out)
end

return TextCase
