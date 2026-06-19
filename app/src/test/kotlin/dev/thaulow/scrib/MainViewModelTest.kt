package dev.thaulow.scrib

import androidx.lifecycle.SavedStateHandle
import dev.thaulow.scrib.data.NoteRepository
import dev.thaulow.scrib.data.UndoStackRepository
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.resetMain
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.test.setMain
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Before
import org.junit.Rule
import org.junit.Test
import org.junit.rules.TemporaryFolder
import java.io.File

@OptIn(ExperimentalCoroutinesApi::class)
class MainViewModelTest {
  @get:Rule
  val tmp = TemporaryFolder()

  private val dispatcher = StandardTestDispatcher()

  @Before
  fun setUp() {
    kotlinx.coroutines.Dispatchers.setMain(dispatcher)
  }

  @After
  fun tearDown() {
    kotlinx.coroutines.Dispatchers.resetMain()
  }

  @Test
  fun `replaceWith before initial load keeps local value`() =
    runTest(dispatcher) {
      val noteFile = File(tmp.root, "scrib.txt").also { it.writeText("persisted") }
      val viewModel =
        MainViewModel(
          NoteRepository(noteFile),
          UndoStackRepository(File(tmp.root, "scrib.undo.json")),
          SavedStateHandle(),
        )

      viewModel.replaceWith("local change")
      advanceUntilIdle()

      assertEquals("local change", viewModel.value.text)
    }

  @Test
  fun `failed flush keeps pending save for retry`() =
    runTest(dispatcher) {
      val blockedParent = tmp.newFile("blocked-parent")
      val viewModel =
        MainViewModel(
          NoteRepository(File(blockedParent, "scrib.txt")),
          UndoStackRepository(File(blockedParent, "scrib.undo.json")),
          SavedStateHandle(),
        )

      var errorCount = 0
      val collector = launch { viewModel.saveError.collect { errorCount += 1 } }

      viewModel.replaceWith("needs saving")
      advanceUntilIdle()

      viewModel.flushPendingSave()
      advanceUntilIdle()
      viewModel.flushPendingSave()
      advanceUntilIdle()

      assertEquals(2, errorCount)
      collector.cancel()
    }
}
