import React, { useState } from 'react';
import { Box, Text } from 'ink';
import { ingestDocument } from '../../knowledge/api.js';

export const IngestionWorkflow: React.FC = () => {
  const [filePath, setFilePath] = useState('');

  const handleIngest = async () => {
    await ingestDocument(filePath);
  };

  return (
    <Box flexDirection="column" borderStyle="round" padding={1}>
      <Text>Ingest Document</Text>
      {/* Basic file input for now, will be improved */}
    </Box>
  );
};
