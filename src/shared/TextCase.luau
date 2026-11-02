-- Заглавные буквы для русского текста: string.upper в Luau меняет только латиницу, кириллицу оставляет строчной.
-- Ни от чего не зависит.

local TextCase = {}

function TextCase.Upper(text: string): string
	local out = {}
	for _, code in utf8.codes(text) do
		if code >= 0x0430 and code <= 0x044F then
			code -= 0x20 -- а…я → А…Я
		elseif code == 0x0451 then
			code = 0x0401 -- ё → Ё
		elseif code >= 0x61 and code <= 0x7A then
			code -= 0x20 -- латиница
		end
		table.insert(out, utf8.char(code))
	end
	return table.concat(out)
end

return TextCase
