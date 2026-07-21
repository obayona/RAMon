<?php

declare(strict_types=1);

namespace Ramon\Chatbot\Tests\Unit\Sync;

use PHPUnit\Framework\TestCase;
use Ramon\Chatbot\Domain\ProductData;
use Ramon\Chatbot\Services\JwtService;
use Ramon\Chatbot\Services\SyncService;
use Ramon\Chatbot\Sync\InitialSync;
use Ramon\Chatbot\Tests\Mocks\MockClock;
use Ramon\Chatbot\Tests\Mocks\MockCronScheduler;
use Ramon\Chatbot\Tests\Mocks\MockHttpClient;
use Ramon\Chatbot\Tests\Mocks\MockInitialSyncRepository;
use Ramon\Chatbot\Tests\Mocks\MockOptionStore;
use Ramon\Chatbot\Tests\Mocks\MockProductExtractor;
use Ramon\Chatbot\Tests\Mocks\MockProductQuery;
use Ramon\Chatbot\Tests\Mocks\MockSiteIterator;
use Ramon\Chatbot\Tests\Mocks\MockTransientStore;

final class InitialSyncTest extends TestCase
{
    private MockOptionStore $options;
    private MockClock $clock;
    private MockHttpClient $http;
    private MockInitialSyncRepository $repo;
    private MockProductExtractor $extractor;
    private MockCronScheduler $cron;
    private MockProductQuery $productQuery;
    private MockTransientStore $transients;
    private MockSiteIterator $sites;
    private InitialSync $sync;

    protected function setUp(): void
    {
        $this->options = new MockOptionStore();
        $this->clock = new MockClock();
        $this->http = new MockHttpClient();
        $this->repo = new MockInitialSyncRepository();
        $this->extractor = new MockProductExtractor();
        $this->cron = new MockCronScheduler();
        $this->productQuery = new MockProductQuery();
        $this->transients = new MockTransientStore();
        $this->sites = new MockSiteIterator();

        $jwt = new JwtService($this->options);
        $syncService = new SyncService($this->options, $this->http, $jwt);

        $this->sync = new InitialSync(
            $this->options,
            $this->clock,
            $syncService,
            $this->extractor,
            $this->repo,
            $this->cron,
            $this->productQuery,
            $this->transients,
            $this->sites,
            batchSize: 2,
        );
    }

    // ------------------------------------------------------------------
    // processCron — guard clauses
    // ------------------------------------------------------------------

    public function testProcessCronSkipsWhenStatusNotRunning(): void
    {
        $this->options->load(['ramon_initial_sync_status' => 'idle']);

        $this->sync->processCron();

        $this->assertFalse($this->repo->tableExists());
        $this->assertSame(0, $this->http->getRequestCount());
    }

    public function testProcessCronSkipsWhenLocked(): void
    {
        $this->options->load([
            'ramon_initial_sync_status' => 'running',
            'ramon_initial_sync_locked' => true,
        ]);

        $this->sync->processCron();

        $this->assertFalse($this->repo->tableExists());
    }

    // ------------------------------------------------------------------
    // processCron — table creation + population
    // ------------------------------------------------------------------

    public function testProcessCronCreatesTableAndPopulatesOnFirstRun(): void
    {
        $this->options->load(['ramon_initial_sync_status' => 'running']);
        $this->productQuery->setProducts([10, 20, 30]);

        $this->sync->processCron();

        $this->assertTrue($this->repo->tableExists());
        $this->assertSame(3, $this->options->get('ramon_initial_sync_total', 0));
        $this->assertSame(0, $this->options->get('ramon_initial_sync_done', 0));
        $this->assertSame(0, $this->options->get('ramon_initial_sync_errors', 0));
    }

    public function testProcessCronSkipsTableCreationWhenAlreadyExists(): void
    {
        $this->options->load(['ramon_initial_sync_status' => 'running']);
        $this->repo->createTable();
        $this->repo->insertProductIds([1, 2]);
        $this->repo->markStatus([1, 2], 'done');

        $this->sync->processCron();

        // Table should still exist, no new products inserted
        $this->assertTrue($this->repo->tableExists());
        $this->assertSame(0, $this->repo->countPending());
    }

    // ------------------------------------------------------------------
    // processCron — batch processing
    // ------------------------------------------------------------------

    public function testProcessCronProcessesBatchAndSendsToBackend(): void
    {
        $this->options->load([
            'ramon_initial_sync_status' => 'running',
            'ramon_api_url' => 'https://api.example.com',
            'ramon_app_key' => 'test-secret',
        ]);
        $this->productQuery->setProducts([10, 20]);

        $data1 = new ProductData(productId: '10', sku: 'SKU-10', name: 'A', description: 'd', categories: '', price: 1.00, stock: 0, inStock: true, url: '', imageUrl: '', status: 'publish');
        $data2 = new ProductData(productId: '20', sku: 'SKU-20', name: 'B', description: 'd', categories: '', price: 2.00, stock: 0, inStock: true, url: '', imageUrl: '', status: 'publish');
        $this->extractor->setProducts([10 => $data1, 20 => $data2]);

        $this->http->setResponse(200, '{"success": true}');

        $this->sync->processCron();

        $this->assertSame(1, $this->http->getRequestCount());
        $this->assertSame(2, $this->options->get('ramon_initial_sync_done', 0));
        $this->assertSame(0, $this->options->get('ramon_initial_sync_errors', 0));
    }

    public function testProcessCronMarksErrorOnBackendFailure(): void
    {
        $this->options->load([
            'ramon_initial_sync_status' => 'running',
            'ramon_api_url' => 'https://api.example.com',
            'ramon_app_key' => 'test-secret',
        ]);
        $this->productQuery->setProducts([10]);

        $data = new ProductData(productId: '10', sku: 'SKU-10', name: 'A', description: 'd', categories: '', price: 1.00, stock: 0, inStock: true, url: '', imageUrl: '', status: 'publish');
        $this->extractor->setProducts([10 => $data]);
        $this->http->setResponse(500, 'Internal Server Error');

        $this->sync->processCron();

        $rows = $this->repo->getRows();
        $this->assertSame('error', $rows[0]['status']);
        $this->assertStringContainsString('HTTP 500', $rows[0]['error'] ?? '');
        $this->assertSame(1, $this->options->get('ramon_initial_sync_errors', 0));
    }

    public function testProcessCronSkipsProductsNotExtracted(): void
    {
        $this->options->load(['ramon_initial_sync_status' => 'running']);
        $this->productQuery->setProducts([10, 20]);
        // extractor returns nothing — simulate deleted/trashed products

        $this->sync->processCron();

        // No HTTP call made, products marked done (no data = skip)
        $this->assertSame(0, $this->http->getRequestCount());
    }

    // ------------------------------------------------------------------
    // processCron — finalization
    // ------------------------------------------------------------------

    public function testProcessCronFinalizesWhenAllProductsProcessed(): void
    {
        $this->options->load([
            'ramon_initial_sync_status' => 'running',
            'ramon_api_url' => 'https://api.example.com',
            'ramon_app_key' => 'test-secret',
            'ramon_chatbot_needs_initial_sync' => true,
        ]);
        $this->productQuery->setProducts([10]);

        $data = new ProductData(productId: '10', sku: 'SKU-10', name: 'A', description: 'd', categories: '', price: 1.00, stock: 0, inStock: true, url: '', imageUrl: '', status: 'publish');
        $this->extractor->setProducts([10 => $data]);
        $this->http->setResponse(200, '{"success": true}');
        $this->cron->schedule(InitialSync::cronHook(), 1700000000, 'one_minute');

        $this->sync->processCron();

        $this->assertSame('complete', $this->options->get('ramon_initial_sync_status', ''));
        $this->assertFalse((bool) $this->options->get('ramon_chatbot_needs_initial_sync', false));
        $this->assertTrue($this->transients->has('ramon_drop_initial_sync_table'));
        $this->assertFalse($this->cron->isScheduled(InitialSync::cronHook()));
    }

    public function testProcessCronKeepsTableWhenErrorsExist(): void
    {
        $this->options->load([
            'ramon_initial_sync_status' => 'running',
            'ramon_api_url' => 'https://api.example.com',
            'ramon_app_key' => 'test-secret',
        ]);
        $this->productQuery->setProducts([10]);

        $data = new ProductData(productId: '10', sku: 'SKU-10', name: 'A', description: 'd', categories: '', price: 1.00, stock: 0, inStock: true, url: '', imageUrl: '', status: 'publish');
        $this->extractor->setProducts([10 => $data]);
        $this->http->setResponse(500, 'Internal Server Error');

        $this->sync->processCron();

        $this->assertSame('complete', $this->options->get('ramon_initial_sync_status', ''));
        $this->assertFalse($this->transients->has('ramon_drop_initial_sync_table'), 'Table drop should not be scheduled when errors exist');
        $this->assertSame(1, $this->options->get('ramon_initial_sync_errors', 0));
    }

    public function testProcessCronUnlocksAfterProcessing(): void
    {
        $this->options->load(['ramon_initial_sync_status' => 'running']);
        $this->productQuery->setProducts([]);

        $this->sync->processCron();

        $this->assertFalse($this->options->has('ramon_initial_sync_locked'));
    }

    // ------------------------------------------------------------------
    // onActivate
    // ------------------------------------------------------------------

    public function testOnActivateSingleSiteSetsRunningStatusAndSchedulesCron(): void
    {
        $this->sync->onActivate(false);

        $this->assertSame('running', $this->options->get('ramon_initial_sync_status', ''));
        $this->assertTrue((bool) $this->options->get('ramon_chatbot_needs_initial_sync', false));
        $this->assertTrue($this->cron->isScheduled(InitialSync::cronHook()));
        $this->assertSame(0, $this->sites->getInvocationCount());
    }

    public function testOnActivateMultisiteIteratesAllSites(): void
    {
        $this->sites->setSiteIds([1, 2, 3]);

        $this->sync->onActivate(true);

        $this->assertSame(3, $this->sites->getInvocationCount());
        $this->assertSame('running', $this->options->get('ramon_initial_sync_status', ''));
        $this->assertTrue($this->cron->isScheduled(InitialSync::cronHook()));
    }

    // ------------------------------------------------------------------
    // onDeactivate
    // ------------------------------------------------------------------

    public function testOnDeactivateUnschedulesCronAndClearsLock(): void
    {
        $this->cron->schedule(InitialSync::cronHook(), 1700000000, 'one_minute');
        $this->options->set('ramon_initial_sync_locked', true);

        $this->sync->onDeactivate();

        $this->assertFalse($this->cron->isScheduled(InitialSync::cronHook()));
        $this->assertFalse($this->options->has('ramon_initial_sync_locked'));
    }

    // ------------------------------------------------------------------
    // maybeProcessSync (admin fallback)
    // ------------------------------------------------------------------

    public function testMaybeProcessSyncSkipsWhenStatusNotRunning(): void
    {
        $this->options->load(['ramon_initial_sync_status' => 'idle']);

        $this->sync->maybeProcessSync();

        $this->assertFalse($this->repo->tableExists());
        $this->assertSame(0, $this->http->getRequestCount());
    }

    public function testMaybeProcessSyncTriggersWhenRunning(): void
    {
        $this->options->load(['ramon_initial_sync_status' => 'running']);
        $this->productQuery->setProducts([]);

        $this->sync->maybeProcessSync();

        // Table should be created (processCron ran)
        $this->assertTrue($this->repo->tableExists());
    }

    // ------------------------------------------------------------------
    // scheduleCron / unscheduleCron
    // ------------------------------------------------------------------

    public function testScheduleCronOnlyIfNotAlreadyScheduled(): void
    {
        $this->sync->scheduleCron();

        $this->assertTrue($this->cron->isScheduled(InitialSync::cronHook()));
    }

    public function testScheduleCronSkipsIfAlreadyScheduled(): void
    {
        $this->cron->schedule(InitialSync::cronHook(), 1700000000, 'one_minute');
        $initialCount = \count($this->cron->getScheduled()[InitialSync::cronHook()] ?? []);

        $this->sync->scheduleCron();

        $finalCount = \count($this->cron->getScheduled()[InitialSync::cronHook()] ?? []);
        $this->assertSame($initialCount, $finalCount);
    }

    public function testUnscheduleCronRemovesScheduledEvent(): void
    {
        $this->cron->schedule(InitialSync::cronHook(), 1700000000, 'one_minute');

        $this->sync->unscheduleCron();

        $this->assertFalse($this->cron->isScheduled(InitialSync::cronHook()));
    }

    public function testUnscheduleCronNoOpWhenNotScheduled(): void
    {
        $this->sync->unscheduleCron();

        $this->assertFalse($this->cron->isScheduled(InitialSync::cronHook()));
    }

    // ------------------------------------------------------------------
    // maybeDropTable
    // ------------------------------------------------------------------

    public function testMaybeDropTableDropsWhenTransientSet(): void
    {
        $this->repo->createTable();
        $this->transients->set('ramon_drop_initial_sync_table', true, 60);

        $this->sync->maybeDropTable();

        $this->assertFalse($this->repo->tableExists());
        $this->assertFalse($this->transients->has('ramon_drop_initial_sync_table'));
    }

    public function testMaybeDropTableNoOpWhenTransientMissing(): void
    {
        $this->repo->createTable();

        $this->sync->maybeDropTable();

        $this->assertTrue($this->repo->tableExists());
    }

    // ------------------------------------------------------------------
    // retryFailed
    // ------------------------------------------------------------------

    public function testRetryFailedReturnsZeroWhenNoErrors(): void
    {
        $this->repo->insertProductIds([1, 2, 3]);
        $this->repo->markStatus([1, 2, 3], 'done');

        $count = $this->sync->retryFailed();

        $this->assertSame(0, $count);
    }

    public function testRetryFailedResetsErrorRowsAndUpdatesOptions(): void
    {
        $this->repo->insertProductIds([1, 2, 3]);
        $this->repo->markStatus([1], 'done');
        $this->repo->markStatus([2, 3], 'error', 'timeout');

        $count = $this->sync->retryFailed();

        $this->assertSame(2, $count);
        $this->assertSame(0, $this->options->get('ramon_initial_sync_errors', ''));
        $this->assertSame('running', $this->options->get('ramon_initial_sync_status', ''));
        $this->assertTrue($this->cron->isScheduled(InitialSync::cronHook()));
        $this->assertFalse($this->repo->tableExists(), 'Table should be dropped on retry');
    }

    // ------------------------------------------------------------------
    // getStatus
    // ------------------------------------------------------------------

    public function testGetStatusReturnsIdleByDefault(): void
    {
        $status = $this->sync->getStatus();

        $this->assertSame('idle', $status->status);
        $this->assertSame(0, $status->total);
        $this->assertSame(0, $status->done);
        $this->assertSame(0, $status->percentage);
        $this->assertFalse($status->needsSync);
    }

    public function testGetStatusReflectsStoredValues(): void
    {
        $this->options->load([
            'ramon_initial_sync_status' => 'running',
            'ramon_initial_sync_total' => 200,
            'ramon_initial_sync_done' => 50,
            'ramon_initial_sync_errors' => 10,
            'ramon_initial_sync_time' => '2024-01-15 12:00:00',
        ]);

        $status = $this->sync->getStatus();

        $this->assertSame('running', $status->status);
        $this->assertSame(200, $status->total);
        $this->assertSame(50, $status->done);
        $this->assertSame(10, $status->errors);
        $this->assertSame(30, $status->percentage);
        $this->assertSame('2024-01-15 12:00:00', $status->time);
    }

    public function testGetStatusNeedsSyncFlag(): void
    {
        $this->options->load([
            'ramon_chatbot_needs_initial_sync' => true,
        ]);

        $status = $this->sync->getStatus();

        $this->assertTrue($status->needsSync);
    }

    // ------------------------------------------------------------------
    // cronHook constant
    // ------------------------------------------------------------------

    public function testCronHookConstant(): void
    {
        $this->assertSame('ramon_initial_sync_hook', InitialSync::cronHook());
    }
}
