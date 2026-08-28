#include "m2fix.h"
#include "sqhook.h"
#include "ketchup.h"

#include "sqemutask.h"
#include "sqglobals.h"
#include "sqsystemdata.h"

template <Squirk Q>
bool Ketchup<Q>::ApplyBlock(HSQUIRRELVM<Q> v,
	Ketchup_TitleInfo &title, Ketchup_VersionInfo &version, Ketchup_DiskInfo &disk,
	uint64_t offset, unsigned char *data, size_t size)
{
	Sqrat::Array<Q> block(v, size);
	for (size_t i = 0; i < size; i++) {
		block.SetValue(i, data[i]);
	}
#ifndef _WIN64
	SQEmuTask<Q>::EntryCdRomPatch(static_cast<SQInteger>(offset), block);
#else
	SQEmuTask<Q>::EntryCdRomPatch(static_cast<SQInteger>(offset), false, block);
#endif
	spdlog::info("[SQ] [Ketchup] CD-ROM write 0x{:08x} with {} bytes.", offset, size);

	// The CD-ROM write above is enough for anything the game reads off the disc
	// at runtime (stage overlays, RADIO.DAT and friends), but not for the boot
	// executable: the Master Collection never reads that from the disc, it
	// preloads it from a ROM snapshot. Those bytes have to be written straight
	// to machine memory instead - and writing them here does not stick, because
	// the Master Collection finishes setting up machine memory *after* the disk
	// patch is entered and discards most of it. So collect the mapped writes
	// and let Update() apply them once the machine is actually up.
	for (size_t i = 0; i < size; i++) {
		uint64_t position = offset + i;
		if (position < disk.ram_base || position >= (disk.ram_base + disk.ram_range))
			continue;

		unsigned int address = static_cast<unsigned int>(position - disk.ram_base);
		unsigned int sector = address / PSX_SectorRange;
		unsigned int pos = address % PSX_SectorRange;
		if (pos >= PSX_SectorSize) continue;

		unsigned int ram = PSX_ImageBase + (sector * PSX_SectorSize) + pos;

		// Coalesce runs so verification stays cheap.
		if (!RamPatches.empty()) {
			auto &last = RamPatches.back();
			if (last.address + last.data.size() == ram) {
				last.data.push_back(data[i]);
				continue;
			}
		}
		RamPatches.push_back({ ram, { data[i] } });
	}

	return true;
}

template <Squirk Q>
void Ketchup<Q>::Update()
{
	if (RamPatches.empty()) return;

	// Mid disc swap - the image is being torn down, leave it alone.
	if (SQHook<Q>::IsCdRomShellOpen()) return;

	// Back off if it refuses to stick, so a pathological case degrades into a
	// slow retry instead of rewriting the image several times a second.
	unsigned int interval = RamCheckInterval * (RamApplies < 8 ? 1 : 16);
	if (RamTick++ % interval != 0) return;

	// Cheap check: one byte per run. Anything wrong and we rewrite the lot.
	// GetRamValue is masked because the value arrives widened, and comparing
	// the raw result against a byte does not reliably hold.
	bool intact = true;
	for (auto &patch : RamPatches) {
		if ((SQEmuTask<Q>::GetRamValue(CHAR_BIT, patch.address) & 0xFF) != patch.data.front()) {
			intact = false;
			break;
		}
	}
	if (intact) return;

	size_t bytes = 0;
	for (auto &patch : RamPatches) {
		for (size_t i = 0; i < patch.data.size(); i++) {
			SQEmuTask<Q>::SetRamValue(CHAR_BIT, patch.address + i, patch.data[i]);
		}
		bytes += patch.data.size();
	}

	// Only worth logging the first few; after that it is a reapply loop and the
	// log would drown in it.
	if (++RamApplies <= 4) {
		spdlog::info("[SQ] [Ketchup] Applied {} bytes of RAM patches in {} blocks (pass {}).",
			bytes, RamPatches.size(), RamApplies);
	}
}

template <Squirk Q>
int Ketchup<Q>::MetaPPF_FileId(std::ifstream &data, int version)
{
	unsigned int magic;
	int length;

	int index = 0;
	if (version == 2) {
		index = 4;
	} else {
		index = 2;
	}

	data.seekg(-(index + 4), std::ios_base::end);
	data.read(reinterpret_cast<char *>(&magic), sizeof(magic));

	if (magic != 'ZID.') {
		return 0;
	}

	data.seekg(-index, std::ios_base::end);
	data.read(reinterpret_cast<char *>(&length), index);
	return length;
}

template <Squirk Q>
bool Ketchup<Q>::ApplyPPF3(HSQUIRRELVM<Q> v, Ketchup_TitleInfo &title, Ketchup_VersionInfo &version, Ketchup_DiskInfo &disk, std::ifstream &data)
{
	unsigned char ppfmem[512];
	int length = MetaPPF_FileId(data, 3);

	unsigned char image_type, block_check, undo;
	data.seekg(56, std::ios_base::beg);
	data.read(reinterpret_cast<char *>(&image_type), sizeof(image_type));
	data.read(reinterpret_cast<char *>(&block_check), sizeof(block_check));
	data.read(reinterpret_cast<char *>(&undo), sizeof(undo));

	data.seekg(0, std::ios_base::end);
	std::streampos count = data.tellg();
	data.seekg(0, std::ios_base::beg);

	std::streampos pos;
	if (block_check) {
		pos = 1084;
		count -= 1084;
	} else {
		pos = 60;
		count -= 60;
	}

	if (length)
		count -= (length + 18 + 16 + 2);

	uint64_t offset;
	unsigned char anz;
	data.seekg(pos, std::ios_base::beg);
	do {
		data.read(reinterpret_cast<char *>(&offset), sizeof(offset));
		data.read(reinterpret_cast<char *>(&anz), sizeof(anz));
		data.read(reinterpret_cast<char *>(ppfmem), anz);
		if (undo) data.seekg(anz, std::ios_base::cur);

		if (!ApplyBlock(v, title, version, disk, offset, ppfmem, anz))
			return false;

		count -= (anz + 9);
		if (undo) count -= anz;
	} while (count != 0);

	return true;
}

template <Squirk Q>
bool Ketchup<Q>::Apply(HSQUIRRELVM<Q> v, Ketchup_TitleInfo &title, Ketchup_VersionInfo &version, Ketchup_DiskInfo &disk, std::ifstream &data)
{
	unsigned int magic;
	data.seekg(0, std::ios_base::beg);
	data.read(reinterpret_cast<char *>(&magic), sizeof(magic));

	switch (magic) {
		case '3FPP': return ApplyPPF3(v, title, version, disk, data);
		default: return false;
	}
}

template <Squirk Q>
std::filesystem::path Ketchup<Q>::RootPath(Ketchup_TitleInfo &title, Ketchup_VersionInfo &version, Ketchup_DiskInfo &disk, std::string base)
{
	std::filesystem::path root(base);
	root /= title.name;
	if (title.versions.size() > 1)
		root /= version.name;
	if (version.disks.size() > 1) {
		char no[] = "0";
		*no += disk.id;
		root /= no;
	}

	return root;
}

template <Squirk Q>
bool Ketchup<Q>::ProcessDisk(HSQUIRRELVM<Q> v, Ketchup_TitleInfo &title, Ketchup_VersionInfo &version, Ketchup_DiskInfo &disk)
{
	std::filesystem::directory_entry root { RootPath(title, version, disk) };
	spdlog::info("[SQ] [Ketchup] base path is {}.", root.path().string());

	if (!root.exists() || !root.is_directory()) return true;
	for (const auto &entry : std::filesystem::directory_iterator(root)) {
		std::ifstream data(entry.path(), std::ios::in | std::ios::binary);
		if (Apply(v, title, version, disk, data)) {
			spdlog::info("[SQ] [Ketchup] loaded {}.", entry.path().string());
		}
	}

	return true;
}

template <Squirk Q>
bool Ketchup<Q>::ProcessVersion(HSQUIRRELVM<Q> v, Ketchup_TitleInfo &title, Ketchup_VersionInfo &version)
{
	for (auto &disk : version.disks) {
		if (disk.id != SQGlobals<Q>::GetDisk()) continue;
		return ProcessDisk(v, title, version, disk);
	}

	return false;
}

template <Squirk Q>
bool Ketchup<Q>::ProcessTitle(HSQUIRRELVM<Q> v, Ketchup_TitleInfo &title)
{
	for (auto &version : title.versions) {
		if (version.name != SQSystemData<Q>::SettingETC::GetVersion()) continue;
		return ProcessVersion(v, title, version);
	}

	return false;
}

template <Squirk Q>
bool Ketchup<Q>::Process(HSQUIRRELVM<Q> v)
{
	// Rebuilt from scratch on every disk patch setup, so a title or disk change
	// cannot leave stale writes aimed at the previous image.
	RamPatches.clear();
	RamTick = 0;
	RamApplies = 0;

	auto *titles = M2Fix::GameInstance().SQKetchupHook();
	if (!titles) return false;

	for (auto &title : *titles) {
		if (title.id != SQGlobals<Q>::GetTitle()) continue;
		return ProcessTitle(v, title);
	}

	return false;
}

template bool Ketchup<Squirk::Standard>::Process(HSQUIRRELVM<Squirk::Standard> v);
template bool Ketchup<Squirk::AlignObject>::Process(HSQUIRRELVM<Squirk::AlignObject> v);
template bool Ketchup<Squirk::StandardShared>::Process(HSQUIRRELVM<Squirk::StandardShared> v);
template bool Ketchup<Squirk::AlignObjectShared>::Process(HSQUIRRELVM<Squirk::AlignObjectShared> v);

template void Ketchup<Squirk::Standard>::Update();
template void Ketchup<Squirk::AlignObject>::Update();
template void Ketchup<Squirk::StandardShared>::Update();
template void Ketchup<Squirk::AlignObjectShared>::Update();
