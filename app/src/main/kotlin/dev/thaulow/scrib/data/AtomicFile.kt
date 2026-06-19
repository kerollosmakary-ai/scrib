package dev.thaulow.scrib.data

import java.io.File
import java.io.RandomAccessFile

fun File.writeAtomically(text: String) {
  val parent = parentFile ?: error("File has no parent: $path")
  parent.mkdirs()
  val tmp = File(parent, "$name.tmp")
  try {
    tmp.writeText(text, Charsets.UTF_8)
    RandomAccessFile(tmp, "rws").use { it.fd.sync() }
    if (exists() && !delete()) {
      throw IllegalStateException("Could not replace existing file: $path")
    }
    if (!tmp.renameTo(this)) {
      throw IllegalStateException("Could not move temp file into place: $path")
    }
  } catch (e: Exception) {
    tmp.delete()
    throw e
  }
}
